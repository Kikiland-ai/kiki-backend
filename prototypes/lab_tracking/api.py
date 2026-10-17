"""FastAPI transport. Domain rules and provider calls live in Python services."""

import base64
import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response, StreamingResponse

from contracts.lab_tracking import AttachCapture, CheckFrame, ContextChange, ReviewCriteria, StartLab, StudentResponse
from .definition import DEFINITION
from .guided import POLICY


def lab_router(service, owner_of, mutation_origin):
    router = APIRouter()

    async def body(request, model):
        mutation_origin(request)
        data = bytearray()
        async for chunk in request.stream():
            data.extend(chunk)
            if len(data) > 12000:
                raise HTTPException(413, "Lab request is too large")
        try:
            return model.model_validate_json(data)
        except ValueError:
            # Avoid echoing arbitrary student reports into validation/logging output.
            raise HTTPException(422, "Invalid lab request fields") from None

    @router.get("/lab-definition")
    async def definition(request: Request):
        owner_of(request)
        return DEFINITION

    @router.get('/lab-guidance-policy')
    async def guidance_policy(request: Request):
        owner_of(request)
        return POLICY

    @router.post("/mcp")
    async def mcp(request: Request):
        data = bytearray()
        async for chunk in request.stream():
            data.extend(chunk)
            if len(data) > 12000:
                raise HTTPException(413, "MCP request too large")
        try:
            rpc = json.loads(data)
            if not isinstance(rpc, dict):
                raise ValueError()
        except ValueError:
            raise HTTPException(422, "Invalid MCP request") from None
        def result(value):
            return {'jsonrpc': '2.0', 'id': rpc.get('id'), 'result': value}
        method = rpc.get('method')
        if method == 'initialize':
            return result({'protocolVersion': '2024-11-05', 'capabilities': {'tools': {}}, 'serverInfo': {'name': 'kiki-dsb-lab-python', 'version': '0.1.0'}})
        if method == 'notifications/initialized':
            return Response(status_code=202)
        if method == 'tools/list':
            tools = [{'name': 'list_lab_sessions', 'description': 'List owned Python DSB-SC prototype runs.',
                      'inputSchema': {'type': 'object', 'properties': {}, 'additionalProperties': False}}]
            for name, description in [('read_lab_session', 'Read owned reviewed progress and current/next instructions.'),
                                      ('read_checked_frame', 'Read fresh latest checked pixels; not continuous video.')]:
                tools.append({'name': name, 'description': description, 'inputSchema': {'type': 'object',
                    'properties': {'lab_session_id': {'type': 'string'}}, 'required': ['lab_session_id'], 'additionalProperties': False}})
            tools.append({'name':'reset_lab_session','description':'Return an owned active or paused lab to step 1 while preserving journal/evidence. Use only on an explicit reset request; read current revision first.','annotations':{'readOnlyHint':False,'destructiveHint':False,'idempotentHint':False},'inputSchema':{'type':'object','properties':{'lab_session_id':{'type':'string'},'revision':{'type':'integer','minimum':1}},'required':['lab_session_id','revision'],'additionalProperties':False}})
            return result({'tools': tools})
        if method != 'tools/call':
            return {'jsonrpc': '2.0', 'id': rpc.get('id'), 'error': {'code': -32601, 'message': 'Method not found'}}
        owner = owner_of(request)
        params = rpc.get('params')
        if not isinstance(params, dict) or not isinstance(params.get('arguments', {}), dict):
            raise HTTPException(422, 'Invalid tool parameters')
        name, args = params.get('name'), params.get('arguments', {})
        if name == 'list_lab_sessions':
            return result({'content': [{'type': 'text', 'text': json.dumps([{'lab_session_id': s['lab_session_id'], 'status': s['status'], 'current_checkpoint_id': s['queue']['current_checkpoint_id']} for s in service.store.list(owner)])}]})
        if name not in ('read_lab_session', 'read_checked_frame', 'reset_lab_session') or not isinstance(args.get('lab_session_id'), str):
            raise HTTPException(422, 'Unknown tool or invalid lab ID')
        lab_id = args['lab_session_id']
        state = service.load(lab_id, owner)
        if name == 'reset_lab_session':
            if set(args) != {'lab_session_id','revision'}:
                raise HTTPException(422,'Invalid reset fields')
            try:
                command=ContextChange(revision=args['revision'],action='revisit',checkpoint_id='CP-DSB-01')
            except ValueError:
                raise HTTPException(422,'Invalid reset revision') from None
            return result({'content':[{'type':'text','text':json.dumps(service.change(lab_id,owner,command))}]})
        if name == 'read_lab_session':
            return result({'content': [{'type': 'text', 'text': json.dumps(service.project(state))}]})
        try:
            image, candidate = service.image(lab_id, owner)
        except HTTPException as error:
            if error.status_code != 410:
                raise
            return result({'isError': True, 'content': [{'type': 'text', 'text': 'No fresh checked pixels. Check the current step again.'}]})
        return result({'content': [{'type': 'text', 'text': json.dumps({'frame_id': candidate['source_frame']['frame_id'], 'observation_id': candidate['observation_id'], 'source_frame': candidate['source_frame'], 'admitted_context': candidate['admitted_context'], 'continuous_live_video': False})},
                                  {'type': 'image', 'mimeType': 'image/jpeg', 'data': base64.b64encode(image).decode()}]})

    @router.post("/lab-sessions", status_code=201)
    async def start(request: Request):
        return service.start(owner_of(request), await body(request, StartLab))

    @router.get("/lab-sessions")
    async def sessions(request: Request):
        return [{"lab_session_id": s["lab_session_id"], "status": s["status"], "model_name": s["workspace"]["model_name"],
                 "current_checkpoint_id": s["queue"]["current_checkpoint_id"]} for s in service.store.list(owner_of(request))]

    @router.get("/lab-sessions/{lab_id}")
    async def read(lab_id: str, request: Request):
        return service.project(service.load(lab_id, owner_of(request)))

    @router.get("/lab-sessions/{lab_id}/events")
    async def events(lab_id: str, request: Request, after: int = 0, limit: int = 100):
        if after < 0 or not 1 <= limit <= 100:
            raise HTTPException(422, "Invalid journal page")
        return service.store.events(lab_id, owner_of(request), after, limit)

    @router.get("/lab-sessions/{lab_id}/export")
    async def export(lab_id: str, request: Request):
        owner = owner_of(request)
        state = service.project(service.load(lab_id, owner))
        through = state['revision']
        def chunks():
            yield '{"definition":'+json.dumps(DEFINITION)+',"state":'+json.dumps(state)+',"events":['
            after, first = 0, True
            while True:
                page = service.store.events(lab_id, owner, after, 100)
                for event in page:
                    if event['event_sequence'] > through:
                        break
                    yield ('' if first else ',')+json.dumps(event)
                    first = False
                if not page or len(page) < 100 or page[-1]['event_sequence'] >= through:
                    break
                after = page[-1]['event_sequence']
            yield ']}'
        return StreamingResponse(chunks(), media_type='application/json', headers={'Cache-Control':'no-store'})

    @router.post("/lab-sessions/{lab_id}/attach")
    async def attach(lab_id: str, request: Request):
        return service.attach(lab_id, owner_of(request), await body(request, AttachCapture))

    @router.post("/lab-sessions/{lab_id}/check")
    async def check(lab_id: str, request: Request):
        return await service.check(lab_id, owner_of(request), await body(request, CheckFrame))

    @router.post("/lab-sessions/{lab_id}/review")
    async def review(lab_id: str, request: Request):
        return service.review(lab_id, owner_of(request), await body(request, ReviewCriteria))

    @router.post("/lab-sessions/{lab_id}/responses")
    async def respond(lab_id: str, request: Request):
        return service.respond(lab_id, owner_of(request), await body(request, StudentResponse))

    @router.post("/lab-sessions/{lab_id}/context")
    async def change(lab_id: str, request: Request):
        return service.change(lab_id, owner_of(request), await body(request, ContextChange))

    def pixels(lab_id, request, handle=None):
        image, candidate = service.image(lab_id, owner_of(request), handle)
        provenance = {k: candidate[k] for k in ("observation_id", "source_frame", "admitted_context", "admitted_at", "completed_at", "frame_handle")}
        return Response(image, media_type="image/jpeg", headers={"Cache-Control": "no-store", "X-Frame-Provenance": base64.b64encode(json.dumps(provenance).encode()).decode()})

    @router.get("/lab-sessions/{lab_id}/image")
    async def image(lab_id: str, request: Request):
        return pixels(lab_id, request)

    @router.get("/lab-sessions/{lab_id}/frame-handles/{handle_id}")
    async def handle(lab_id: str, handle_id: str, request: Request):
        return pixels(lab_id, request, handle_id)

    @router.delete("/lab-sessions/{lab_id}")
    async def delete(lab_id: str, request: Request):
        mutation_origin(request)
        service.store.delete(lab_id, owner_of(request))
        service.images.pop(lab_id, None)
        return {"deleted": True}

    return router
