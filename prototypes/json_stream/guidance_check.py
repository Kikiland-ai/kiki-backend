"""Opt-in orchestration export for a future owned FastAPI SSE adapter."""
import time,json
from copy import deepcopy
from .drawing_context import DRAWING_RUN
from .guidance import committed_state,instant
from .analysis import STREAM_SINK

async def check_with_drawing(service, lab_id, owner, body, *, run, outbox,
                             stream_id, project_runtime):
    """Use actual tracker checks/save, then revision-guard the durable drawing outbox.

    Existing SSE sink must be installed by the owned route. This helper does not
    negotiate headers, authenticate an extension, deliver an event or await paint.
    project_runtime runs inside the outbox transaction; derive fresh tracker text.
    """
    if STREAM_SINK.get() is None:
        raise ValueError('owned_stream_sink_required')
    started=time.monotonic()
    token=DRAWING_RUN.set(run)
    try:
        state=await service.check(lab_id,owner,body)
        if run.model is None or state['runtime'].get('analysis_status')!='available':
            return {'type':'analysis_waiting','state':state}
        commit_finished_ms=round((time.monotonic()-started)*1000)
        if run.trace:
            run.trace.emit('tracker_committed',commit_finished_ms=commit_finished_ms,
                           **{k:v for k,v in state['runtime']['last_analysis_timing'].items() if k!='commit_finished_ms'})
        packet_started=time.monotonic()
        payload=outbox.append(owner=owner,lab_id=lab_id,stream_id=stream_id,
                              expected_revision=state['revision'],project_runtime=project_runtime,
                              admission=run.admission,model=run.model)
        if run.trace:
            run.trace.emit('published',publication_ms=round((time.monotonic()-started)*1000),
                           packet_prepared_ms=round((time.monotonic()-packet_started)*1000),
                           frame_age_at_commit_ms=round((instant(payload['validity']['created_at'])-instant(payload['frame']['received_at'])).total_seconds()*1000),
                           screen_guidance_bytes=len(json.dumps(payload).encode()))
        return {'type':'guidance_committed','provisional':False,'context':run.admission['admitted_context'],
                'current_context':payload['context'],'revision':state['revision'],
                'guidance':deepcopy(state['guidance']),'queue':deepcopy(state['queue']),'status':state['status'],
                'commit_finished_ms':commit_finished_ms,
                'state':committed_state(state,payload)}
    except BaseException as error:
        if run.trace:
            status=getattr(error,'status_code',None)
            cancelled=type(error).__name__=='CancelledError'
            run.trace.emit('cancelled' if cancelled else 'discarded' if status==409 or str(error) in ('stale_context','stale_source_context','revision_conflict','expired_frame') else 'failed',
                           reason='analysis_cancelled' if cancelled else 'stale_context' if status==409 else str(error))
        raise
    finally:
        DRAWING_RUN.reset(token)
