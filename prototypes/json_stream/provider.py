"""Consume the full SSE body while retaining the existing durable key lease."""
import asyncio,json,uuid,os,time
import httpx
from prototypes.lab_tracking.provider import ProviderPool, AnalysisFailure, digest

class StreamingProviderPool(ProviderPool):
    def __init__(self,*args,io_mode=None,**kwargs):
        super().__init__(*args,**kwargs)
        self.io_mode=io_mode or os.environ.get('KIKI_PROVIDER_IO','batched')
    def _measure(self,metrics,count,action):
        started=time.monotonic();metrics['provider_db_operations']+=count if self.db is not None else 0
        try:return action()
        finally:metrics['provider_db_ms']+=(time.monotonic()-started)*1000
    def _acquire(self,owner,metrics):
        if self.io_mode=='serial' or self.db is None:return self._measure(metrics,2,lambda:self.acquire(owner))
        def query():
            now=self.clock()
            with self.lock,self.db:
                row=self.db.execute('INSERT INTO provider_rotation(router_id,lease_owner,lease_until) VALUES(?,?,?) ON CONFLICT(router_id) DO UPDATE SET lease_owner=excluded.lease_owner,lease_until=excluded.lease_until WHERE provider_rotation.lease_until<=? RETURNING last_key,failed_keys,retry_at,lease_owner,lease_until,last_error',(self.router_id,owner,now+30,now)).fetchone()
                return dict(zip(('last_key','failed_keys','retry_at','lease_owner','lease_until','last_error'),row)) if row else None
        return self._measure(metrics,1,query)
    def _persist(self,row,owner,metrics,release=False):
        return self._measure(metrics,1,lambda:self.persist(row,owner,release=release))
    def _health(self,ids,metrics):
        if self.db is None:return {key:self.get(key)[0] for key in ids}
        def query():
            with self.lock:return dict(self.db.execute('SELECT pool_id,retry_at FROM provider_cooldowns WHERE pool_id IN ('+','.join('?' for _ in ids)+')',tuple(ids)).fetchall())
        return self._measure(metrics,1,query)
    async def stream(self,model,body,consume,reset,metrics_sink=None):
        if self.io_mode not in ('serial','batched'):raise AnalysisFailure('invalid_provider_configuration')
        metrics={'provider_io_mode':self.io_mode,'provider_db_operations':0,'provider_db_ms':0,'provider_http_attempts':0,'provider_http_ms':0};all_started=time.monotonic()
        if self.invalid:raise AnalysisFailure('invalid_provider_configuration')
        if not self.keys:raise AnalysisFailure('provider_not_configured')
        owner=str(uuid.uuid4());row=self._acquire(owner,metrics)
        if row is None:raise AnalysisFailure('provider_rotation_busy',int((self.clock()+5)*1000))
        try:
            if row['retry_at']>self.clock():raise AnalysisFailure(row['last_error'] or 'provider_cycle_cooldown',int(row['retry_at']*1000))
            if row['retry_at']:row.update(failed_keys='[]',retry_at=0,last_error=None)
            failed=set(json.loads(row['failed_keys']));deadline=asyncio.get_running_loop().time()+20
            last=row['last_error'] or 'provider_cooldown'
            async with httpx.AsyncClient(timeout=20,transport=self.transport,trust_env=True) as client:
                while True:
                    start=next((i+1 for i,v in enumerate(self.keys) if v['id']==row['last_key']),0)
                    eligible=[];future=[]
                    ids={item['id']:(digest(f"{model}:{item['quota_pool']}"),digest('key:'+item['id']),digest('model:'+model)) for item in self.keys}
                    snapshot=self._health(set(key for values in ids.values() for key in values),metrics) if self.io_mode=='batched' else None
                    for item in self.keys[start:]+self.keys[:start]:
                        quota_id,key_id,model_id=ids[item['id']]
                        retry_at=max(snapshot.get(key,0) for key in ids[item['id']]) if snapshot is not None else max(self._measure(metrics,1,lambda key=key:self.get(key)[0]) for key in ids[item['id']])
                        if len(self.keys)>1 and item['id']==row['last_key']:continue
                        future.append(retry_at)
                        if item['id'] not in failed and retry_at<=self.clock():eligible.append((item,quota_id,key_id,model_id))
                    if not eligible:
                        row.update(retry_at=max(self.clock()+60,min(future) if future else 0),last_error=last,failed_keys=json.dumps(sorted(failed)))
                        self._persist(row,owner,metrics);raise AnalysisFailure(last,int(row['retry_at']*1000))
                    remaining=deadline-asyncio.get_running_loop().time()
                    if remaining<=0:raise AnalysisFailure(last,int((self.clock()+5)*1000))
                    item,quota_id,key_id,model_id=eligible[0];row['last_key']=item['id'];self._persist(row,owner,metrics)
                    status=0;advised=None
                    await reset()
                    http_started=time.monotonic();metrics['provider_http_attempts']+=1;metrics['provider_last_dispatch_ms']=(http_started-all_started)*1000;metrics.setdefault('provider_first_dispatch_ms',metrics['provider_last_dispatch_ms'])
                    try:
                        async with asyncio.timeout(min(remaining,8 if len(self.keys)>1 else 20)):
                            async with client.stream('POST',f'https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?alt=sse',headers={'x-goog-api-key':item['key']},json=body) as response:
                                status=response.status_code;advised=self.retry_after(response.headers.get('retry-after'))
                                metrics['provider_headers_ms']=(time.monotonic()-http_started)*1000
                                if response.is_success:
                                    result=await consume(response)
                                    row.update(failed_keys='[]',retry_at=0,last_error=None)
                                    if self.io_mode=='serial':self._persist(row,owner,metrics)
                                    return result
                                last=f'provider_http_{status}'
                    except (httpx.HTTPError,TimeoutError):
                        status=0;last='provider_timeout_or_network_error'
                    finally:metrics['provider_http_ms']+=(time.monotonic()-http_started)*1000
                    failed.add(item['id']);row.update(failed_keys=json.dumps(sorted(failed)),last_error=last);self._persist(row,owner,metrics)
                    if status==429:self._measure(metrics,1,lambda:self.save(quota_id,self.clock()+max(60,advised or 0)))
                    elif status in (401,403):self._measure(metrics,1,lambda:self.save(key_id,self.clock()+900))
                    elif status and status<500: self._measure(metrics,1,lambda:self.save(model_id,self.clock()+900));raise AnalysisFailure(last,int((self.clock()+900)*1000))
                    elif advised is not None:self._measure(metrics,1,lambda:self.save(key_id,self.clock()+max(10,advised)))
        except BaseException as error:
            error.provider_metrics=metrics
            raise
        finally:
            try:self._persist(row,owner,metrics,release=True)
            finally:
                for key in metrics:
                    if isinstance(metrics[key],(float,int)):metrics[key]=round(metrics[key])
                if metrics_sink is not None:metrics_sink(dict(metrics))
