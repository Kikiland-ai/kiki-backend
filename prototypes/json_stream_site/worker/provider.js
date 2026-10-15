// Persistent reservations serialize outbound selection across Worker isolates.
// Credential values never enter DB, logs or browser responses.
const providerMemory=new WeakMap();
async function providerHash(text){return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text))),v=>v.toString(16).padStart(2,'0')).join('');}
function providerKeys(env){
 let values;try{values=env.GEMINI_API_KEYS?JSON.parse(env.GEMINI_API_KEYS):env.GEMINI_API_KEY?[{key:env.GEMINI_API_KEY,quota_pool:'default'}]:[];}catch{throw Error('invalid_provider_configuration');}
 if(!Array.isArray(values)||values.length>16||(env.GEMINI_API_KEYS&&!values.length))throw Error('invalid_provider_configuration');
 const keys=values.map(v=>typeof v==='string'?{key:v,quota_pool:'default'}:{...v,quota_pool:v?.quota_pool??'default'});
 if(keys.some(v=>typeof v.key!=='string'||!v.key||typeof v.quota_pool!=='string'||!v.quota_pool)||new Set(keys.map(v=>v.key)).size!==keys.length)throw Error('invalid_provider_configuration');
 return keys;
}
function providerConfigured(env){return Boolean(env.GEMINI_API_KEY||env.GEMINI_API_KEYS);}
function providerLocal(env){if(!providerMemory.has(env))providerMemory.set(env,{health:new Map(),rotation:new Map()});return providerMemory.get(env);}
async function providerHealth(env,id,retryAt=null){
 if(env.DB){
  if(retryAt!==null)await env.DB.prepare('INSERT INTO provider_cooldowns(pool_id,retry_at,failures) VALUES(?,?,1) ON CONFLICT(pool_id) DO UPDATE SET retry_at=MAX(retry_at,excluded.retry_at),failures=provider_cooldowns.failures+1').bind(id,retryAt).run();
  return (await env.DB.prepare('SELECT retry_at FROM provider_cooldowns WHERE pool_id=?').bind(id).first())?.retry_at||0;
 }
 const health=providerLocal(env).health;if(retryAt!==null)health.set(id,Math.max(health.get(id)||0,retryAt));return health.get(id)||0;
}
async function providerAcquire(env,id,owner,mode='serial'){
 const now=Date.now();
 if(env.DB){
  if(mode==='batched')return await env.DB.prepare('INSERT INTO provider_rotation(router_id,lease_owner,lease_until) VALUES(?,?,?) ON CONFLICT(router_id) DO UPDATE SET lease_owner=excluded.lease_owner,lease_until=excluded.lease_until WHERE provider_rotation.lease_until<=? RETURNING *').bind(id,owner,now+30000,now).first();
  await env.DB.prepare('INSERT OR IGNORE INTO provider_rotation(router_id) VALUES(?)').bind(id).run();
  return await env.DB.prepare('UPDATE provider_rotation SET lease_owner=?,lease_until=? WHERE router_id=? AND lease_until<=? RETURNING *').bind(owner,now+30000,id,now).first();
 }
 const values=providerLocal(env).rotation;
 if(!values.has(id))values.set(id,{last_key:null,failed_keys:'[]',retry_at:0,lease_owner:null,lease_until:0,last_error:null});
 const row=values.get(id);if(row.lease_until>now)return null;Object.assign(row,{lease_owner:owner,lease_until:now+30000});return {...row};
}
async function providerPersist(env,id,row,owner,release=false){
 if(env.DB){
  const result=await env.DB.prepare('UPDATE provider_rotation SET last_key=?,failed_keys=?,retry_at=?,last_error=?,lease_owner=?,lease_until=? WHERE router_id=? AND lease_owner=?').bind(row.last_key,row.failed_keys,row.retry_at,row.last_error,release?null:owner,release?0:row.lease_until,id,owner).run();
  if(result.meta.changes!==1)throw providerWait('provider_rotation_lease_lost',Date.now()+5000);
 }else{
  const current=providerLocal(env).rotation.get(id);if(current.lease_owner!==owner)throw providerWait('provider_rotation_lease_lost',Date.now()+5000);
  Object.assign(current,row,release?{lease_owner:null,lease_until:0}:{});
 }
}
function providerWait(error,retryAt){return Object.assign(Error(error),{retry_at_ms:retryAt,retry_after_ms:Math.max(0,retryAt-Date.now())});}
function providerRetryAfter(value){
 if(!value)return null;const seconds=Number(value);if(Number.isFinite(seconds)&&seconds>=0)return seconds*1000;
 const date=Date.parse(value);return Number.isFinite(date)?Math.max(0,date-Date.now()):null;
}
function providerMeasuredDB(db,metrics){
 const measured=async action=>{const started=performance.now();metrics.provider_db_operations++;try{return await action();}finally{metrics.provider_db_ms+=performance.now()-started;}};
 const wrap=statement=>({bind(...values){return wrap(statement.bind(...values));},first(...args){return measured(()=>statement.first(...args));},run(...args){return measured(()=>statement.run(...args));},all(...args){return measured(()=>statement.all(...args));}});
 return {prepare(sql){return wrap(db.prepare(sql));}};
}
async function providerHealthSnapshot(env,ids){
 const unique=[...new Set(ids)];
 if(!env.DB)return new Map(unique.map(id=>[id,providerLocal(env).health.get(id)||0]));
 const result=await env.DB.prepare(`SELECT pool_id,retry_at FROM provider_cooldowns WHERE pool_id IN (${unique.map(()=>'?').join(',')})`).bind(...unique).all();
 return new Map(result.results.map(row=>[row.pool_id,row.retry_at]));
}
async function providerRequest(env,model,body,fetcher=fetch,stream=null){
 const mode=env.KIKI_PROVIDER_IO||'batched';if(!['serial','batched'].includes(mode))throw Error('invalid_provider_configuration');
 const metrics={provider_io_mode:mode,provider_db_operations:0,provider_db_ms:0,provider_http_attempts:0,provider_http_ms:0},allStarted=performance.now();
 if(env.DB)env={...env,DB:providerMeasuredDB(env.DB,metrics)};
 const keys=providerKeys(env);if(!keys.length)throw Error('provider_not_configured');
 for(const key of keys)key.id=await providerHash(key.key);
 const routerId=await providerHash('rotation/v1:'+keys.map(v=>v.id+':'+v.quota_pool).sort().join(',')),owner=crypto.randomUUID();
 const row=await providerAcquire(env,routerId,owner,mode);if(!row)throw providerWait('provider_rotation_busy',Date.now()+5000);
 try{
  if(row.retry_at>Date.now())throw providerWait(row.last_error||'provider_cycle_cooldown',row.retry_at);
  if(row.retry_at)Object.assign(row,{failed_keys:'[]',retry_at:0,last_error:null});
  const failed=new Set(JSON.parse(row.failed_keys)),deadline=Date.now()+20000;let last=row.last_error||'provider_cooldown';
  while(true){
   const start=keys.findIndex(v=>v.id===row.last_key)+1,ordered=[...keys.slice(start),...keys.slice(0,start)],eligible=[],future=[];
   const healthIds=mode==='batched'?await Promise.all(ordered.map(async item=>({item,quotaId:await providerHash(model+':'+item.quota_pool),keyId:await providerHash('key:'+item.id),modelId:await providerHash('model:'+model)}))):null;
   const snapshot=healthIds?await providerHealthSnapshot(env,healthIds.flatMap(v=>[v.quotaId,v.keyId,v.modelId])):null;
   for(const item of ordered){
    const ids=healthIds?.find(v=>v.item===item),quotaId=ids?.quotaId||await providerHash(model+':'+item.quota_pool),keyId=ids?.keyId||await providerHash('key:'+item.id),modelId=ids?.modelId||await providerHash('model:'+model);
    const retryAt=snapshot?Math.max(snapshot.get(quotaId)||0,snapshot.get(keyId)||0,snapshot.get(modelId)||0):Math.max(await providerHealth(env,quotaId),await providerHealth(env,keyId),await providerHealth(env,modelId));
    if(keys.length>1&&item.id===row.last_key)continue;
    future.push(retryAt);
    if(failed.has(item.id)||retryAt>Date.now())continue;
    eligible.push({item,quotaId,keyId,modelId});
   }
   if(!eligible.length){
    Object.assign(row,{retry_at:Math.max(Date.now()+60000,future.length?Math.min(...future):0),last_error:last,failed_keys:JSON.stringify([...failed].sort())});
    await providerPersist(env,routerId,row,owner);throw providerWait(last,row.retry_at);
   }
   const remaining=deadline-Date.now();if(remaining<=0){await providerPersist(env,routerId,row,owner);throw providerWait(last,Date.now()+5000);}
   const {item,quotaId,keyId,modelId}=eligible[0];row.last_key=item.id;await providerPersist(env,routerId,row,owner);
   let response,streamResult;const started=Date.now();if(stream)await stream.reset();const httpStarted=performance.now();metrics.provider_http_attempts++;metrics.provider_last_dispatch_ms=httpStarted-allStarted;metrics.provider_first_dispatch_ms??=metrics.provider_last_dispatch_ms;
   try{response=await fetcher(`https://generativelanguage.googleapis.com/v1beta/models/${model}:${stream?'streamGenerateContent?alt=sse':'generateContent'}`,{method:'POST',headers:{'Content-Type':'application/json','x-goog-api-key':item.key},body:JSON.stringify(body),signal:stream?AbortSignal.any([stream.signal,AbortSignal.timeout(Math.min(keys.length>1?8000:20000,remaining))]):AbortSignal.timeout(Math.min(keys.length>1?8000:20000,remaining))});metrics.provider_headers_ms=performance.now()-httpStarted;if(response?.ok&&stream)streamResult=await stream.consume(response);}catch(error){if(stream?.signal.aborted)throw Error('analysis_cancelled');if(['invalid_output','incomplete_output','stale_context'].includes(error.message))throw error;response=null;last='provider_timeout_or_network_error';}finally{metrics.provider_http_ms+=performance.now()-httpStarted;}
   if(response?.ok){Object.assign(row,{failed_keys:'[]',retry_at:0,last_error:null});if(mode==='serial')await providerPersist(env,routerId,row,owner);return stream?streamResult:response;}
   if(response)last=`provider_http_${response.status}`;
   console.error(JSON.stringify({event:'provider_attempt_failed',model,key_id:item.id.slice(0,12),category:last,elapsed_ms:Date.now()-started}));
   failed.add(item.id);Object.assign(row,{failed_keys:JSON.stringify([...failed].sort()),last_error:last});await providerPersist(env,routerId,row,owner);
   const status=response?.status||0,advised=providerRetryAfter(response?.headers.get('retry-after'));
   if(status===429)await providerHealth(env,quotaId,Date.now()+Math.max(60000,advised||0));
   else if(status===401||status===403)await providerHealth(env,keyId,Date.now()+900000);
   else if(status&&status<500){await providerHealth(env,modelId,Date.now()+900000);throw providerWait(last,Date.now()+900000);}
   else if(advised!==null)await providerHealth(env,keyId,Date.now()+Math.max(10000,advised));
  }
 }catch(error){error.provider_metrics=metrics;throw error;}finally{
  try{await providerPersist(env,routerId,row,owner,true);}finally{
   for(const key of Object.keys(metrics))if(typeof metrics[key]==='number')metrics[key]=Math.round(metrics[key]);
   if(typeof stream?.onMetrics==='function')stream.onMetrics({...metrics});
  }
 }
}
export {providerRequest,providerConfigured};
