"""Owned SSE delivery around the existing admission/atomic checkpoint service."""
import asyncio,copy,json
from uuid import uuid4
from fastapi import APIRouter,HTTPException,Request
from fastapi.responses import StreamingResponse
from contracts.lab_tracking import CheckFrame
from .analysis import STREAM_SINK
from prototypes.lab_tracking.provider import AnalysisFailure

def stream_router(service,owner_of,mutation_origin):
    router=APIRouter(tags=['screen-json-stream'])
    @router.post('/lab-sessions/{lab_id}/check-stream',response_class=StreamingResponse,responses={200:{'description':'Owned ordered lab-analysis-stream/v1 SSE events','content':{'text/event-stream':{'schema':{'type':'string'}}}}},openapi_extra={'requestBody':{'required':True,'content':{'application/json':{'schema':CheckFrame.model_json_schema()}}}})
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
        request_id=str(uuid4());queue=asyncio.Queue(maxsize=64);context=None;sequence=0
        async def sink(event):
            nonlocal context
            if event['type']=='admitted':
                context=service.context(event['state'])
                event={'type':'admitted','frame':frame,'admitted_at':service.timestamp(event['state']['runtime']['last_analysis_started'])}
            else:
                current=service.load(lab_id,owner)
                if context is None or service.context(current)!=context or current['status']!='active':
                    raise AnalysisFailure('stale_stream_context')
            await queue.put({**event,'context':context,'provisional':event['type'] not in ('admitted',)})
        async def work():
            token=STREAM_SINK.set(sink)
            try:
                result=await service.check(lab_id,owner,body)
                committed=context is not None and result['runtime'].get('last_analysis_timing',{}).get('status')=='available' and result['runtime'].get('analysis_status')!='waiting_for_provider'
                if committed:
                    await queue.put({'type':'guidance_committed','context':context,'current_context':result['guidance']['context'],'guidance':result['guidance'],'queue':result['queue'],'revision':result['revision'],'status':result['status'],'provisional':False})
                    await queue.put({'type':'state_snapshot','state':result,'context':context,'current_context':result['guidance']['context'],'provisional':False})
                else:await queue.put({'type':'analysis_waiting','state':result,'context':context,'provisional':False})
                await queue.put({'type':'stream_complete','context':context,'timing':result['runtime'].get('last_analysis_timing'),'provisional':False})
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
                    if event.get('provisional') and context is not None:
                        current=service.load(lab_id,owner)
                        if service.context(current)!=context:continue
                    sequence+=1
                    value={'schema':'lab-analysis-stream/v1','request_id':request_id,'event_sequence':sequence,'server_time':service.timestamp(),**event}
                    yield 'data: '+json.dumps(value,ensure_ascii=False)+'\n\n'
            finally:
                if not task.done():task.cancel()
                await asyncio.gather(task,return_exceptions=True)
        return StreamingResponse(deliver(),media_type='text/event-stream',headers={'Cache-Control':'no-store','X-Accel-Buffering':'no'})
    return router
