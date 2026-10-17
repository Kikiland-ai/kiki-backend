"""Owned SSE delivery around the existing admission/atomic checkpoint service."""
import asyncio,copy,json,time,os
from uuid import uuid4
from fastapi import APIRouter,HTTPException,Request
from fastapi.responses import StreamingResponse
from contracts.lab_tracking import CheckFrame
from .analysis import STREAM_SINK
from prototypes.lab_tracking.provider import AnalysisFailure
from .decision import committed_projection
from .context_batch import ContextBatch

def stream_router(service,owner_of,mutation_origin,*,context_mode=None):
    mode=context_mode or os.environ.get("KIKI_STREAM_CONTEXT_MODE","per_chunk")
    if mode not in ("per_chunk","per_event"):raise ValueError("invalid_stream_context_configuration")
    router=APIRouter(tags=['screen-json-stream'])
    @router.post('/lab-sessions/{lab_id}/check-stream',response_class=StreamingResponse,responses={200:{'description':'Owned lab-analysis-stream/v2: complete decision commits before auxiliary delivery','content':{'text/event-stream':{'schema':{'type':'string'}}}}},openapi_extra={'requestBody':{'required':True,'content':{'application/json':{'schema':CheckFrame.model_json_schema()}}}})
    async def check_stream(lab_id:str,request:Request):
        owner=owner_of(request);mutation_origin(request)
        if not getattr(service.analyzer,'supports_stream',False):raise HTTPException(503,'The configured analyzer has no JSON stream adapter')
        raw=bytearray()
        async for chunk in request.stream():
            raw.extend(chunk)
            if len(raw)>12000:raise HTTPException(413,'Lab request too large')
        try:body=CheckFrame.model_validate_json(raw)
        except ValueError:raise HTTPException(422,'Invalid check fields') from None
        state=service.load(lab_id,owner);service.expect(state,body.revision)
        frame=copy.deepcopy(service.capture(state['workspace']['capture_session_id'],owner)['frame'])
        request_id=str(uuid4());queue=asyncio.Queue(maxsize=64);context=None;sequence=0;started=time.monotonic()
        async def publish(group):
            await queue.put([{**event,'context':context,'provisional':True} for event in group])
        def valid(current):
            return context is not None and service.context(current)==context and current['status']=='active' and current['runtime']['capture_status']=='sharing'
        gate=ContextBatch(mode,lambda:service.load(lab_id,owner),valid,publish)
        async def sink(event):
            nonlocal context
            if event['type']=='admitted':
                context=service.context(event['state'])
                await queue.put({'type':'admitted','frame':frame,'admitted_at':service.timestamp(event['state']['runtime']['last_analysis_started']),'context':context,'provisional':False})
            else:await gate.batch([event])
        sink.metrics=gate.metrics
        sink.batch=gate.batch
        async def work():
            token=STREAM_SINK.set(sink)
            try:
                result=await service.check(lab_id,owner,body)
                commit_finished_ms=round((time.monotonic()-started)*1000)
                committed=context is not None and result['runtime'].get('last_analysis_timing',{}).get('status')=='available' and result['runtime'].get('analysis_status')!='waiting_for_provider'
                if committed:
                    await queue.put({'type':'guidance_committed','context':context,'current_context':result['guidance']['context'],'guidance':result['guidance'],'queue':result['queue'],'revision':result['revision'],'status':result['status'],'state':committed_projection(result),'commit_finished_ms':commit_finished_ms,'provisional':False})
                    # Provider and LabService slots are released. Delivery of this tail
                    # has no authority over a later committed decision.
                    await asyncio.sleep(0)
                    hook=getattr(service,'stream_auxiliary_hook',None)
                    if hook is not None:await hook(result)
                    await queue.put({'type':'state_snapshot','state':result,'context':context,'current_context':result['guidance']['context'],'provisional':False})
                else:await queue.put({'type':'analysis_waiting','state':result,'context':context,'provisional':False})
                await queue.put({'type':'stream_complete','context':context,'revision':result['revision'],'timing':{**(result['runtime'].get('last_analysis_timing',{}) if context else {}),'decision_committed':committed,'timing_scope':'new_check' if context else 'retained_state','commit_finished_ms':commit_finished_ms if committed else None,'auxiliary_finished_ms':round((time.monotonic()-started)*1000)},'provisional':False})
            except HTTPException as error:
                await queue.put({'type':'discarded' if error.status_code==409 else 'analysis_failed','context':context,'status':error.status_code,'reason':error.detail,'provisional':False})
            except asyncio.CancelledError:raise
            except Exception:
                await queue.put({'type':'analysis_failed','context':context,'reason':'stream_failure','provisional':False})
            finally:
                STREAM_SINK.reset(token)
                if not asyncio.current_task().cancelling():await queue.put(None)
        async def deliver():
            nonlocal sequence
            task=asyncio.create_task(work())
            try:
                while True:
                    event=await queue.get()
                    if event is None:break
                    group=event if isinstance(event,list) else [event]
                    if any(item.get('provisional') for item in group) and context is not None:
                        load_started=time.monotonic();gate.metrics['context_delivery_db_reads']+=1
                        try:current=service.load(lab_id,owner)
                        finally:gate.metrics['context_delivery_db_ms']+=round((time.monotonic()-load_started)*1000)
                        if not valid(current):continue
                    # One yield for the group: no per-row delivery reads or TTL cache.
                    packets=[]
                    for item in group:
                        if item['type']=='stream_complete':item={**item,'timing':{**item['timing'],**{k:v for k,v in gate.metrics.items() if k.startswith('context_delivery_')}}}
                        sequence+=1
                        value={'schema':'lab-analysis-stream/v2','request_id':request_id,'event_sequence':sequence,'server_time':service.timestamp(),**item}
                        packets.append('data: '+json.dumps(value,ensure_ascii=False)+'\n\n')
                    yield ''.join(packets)
            finally:
                if not task.done():task.cancel()
                await asyncio.gather(task,return_exceptions=True)
        return StreamingResponse(deliver(),media_type='text/event-stream',headers={'Cache-Control':'no-store','X-Accel-Buffering':'no'})
    return router
