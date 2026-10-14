"""Consume the full SSE body while retaining the existing durable key lease."""
import asyncio,json,uuid
import httpx
from prototypes.lab_tracking.provider import ProviderPool, AnalysisFailure, digest

class StreamingProviderPool(ProviderPool):
    async def stream(self,model,body,consume,reset):
        if self.invalid:raise AnalysisFailure('invalid_provider_configuration')
        if not self.keys:raise AnalysisFailure('provider_not_configured')
        owner=str(uuid.uuid4());row=self.acquire(owner)
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
                    for item in self.keys[start:]+self.keys[:start]:
                        quota_id=digest(f"{model}:{item['quota_pool']}");key_id=digest('key:'+item['id']);model_id=digest('model:'+model)
                        retry_at=max(self.get(quota_id)[0],self.get(key_id)[0],self.get(model_id)[0])
                        if len(self.keys)>1 and item['id']==row['last_key']:continue
                        future.append(retry_at)
                        if item['id'] not in failed and retry_at<=self.clock():eligible.append((item,quota_id,key_id,model_id))
                    if not eligible:
                        row.update(retry_at=max(self.clock()+60,min(future) if future else 0),last_error=last,failed_keys=json.dumps(sorted(failed)))
                        self.persist(row,owner);raise AnalysisFailure(last,int(row['retry_at']*1000))
                    remaining=deadline-asyncio.get_running_loop().time()
                    if remaining<=0:raise AnalysisFailure(last,int((self.clock()+5)*1000))
                    item,quota_id,key_id,model_id=eligible[0];row['last_key']=item['id'];self.persist(row,owner)
                    status=0;advised=None
                    await reset()
                    try:
                        async with asyncio.timeout(min(remaining,8 if len(self.keys)>1 else 20)):
                            async with client.stream('POST',f'https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?alt=sse',headers={'x-goog-api-key':item['key']},json=body) as response:
                                status=response.status_code;advised=self.retry_after(response.headers.get('retry-after'))
                                if response.is_success:
                                    result=await consume(response)
                                    row.update(failed_keys='[]',retry_at=0,last_error=None);self.persist(row,owner)
                                    return result
                                last=f'provider_http_{status}'
                    except (httpx.HTTPError,TimeoutError):
                        status=0;last='provider_timeout_or_network_error'
                    failed.add(item['id']);row.update(failed_keys=json.dumps(sorted(failed)),last_error=last);self.persist(row,owner)
                    if status==429:self.save(quota_id,self.clock()+max(60,advised or 0))
                    elif status in (401,403):self.save(key_id,self.clock()+900)
                    elif status and status<500: self.save(model_id,self.clock()+900);raise AnalysisFailure(last,int((self.clock()+900)*1000))
                    elif advised is not None:self.save(key_id,self.clock()+max(10,advised))
        finally:self.persist(row,owner,release=True)
