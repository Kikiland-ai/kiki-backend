"""Physical preparation API; inherits the application's existing auth boundary."""
import re

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import FileResponse
from starlette.responses import JSONResponse

from contracts.physical_lab import CreatePreparation, PreparationEvent
from .service import ROOT


class PhysicalBodyLimit:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or not scope['path'].startswith('/v1/physical-labs'):
            return await self.app(scope, receive, send)
        messages, size = [], 0
        while True:
            message = await receive()
            if message['type'] != 'http.request':
                return
            size += len(message.get('body', b''))
            if size > 16000:
                return await JSONResponse({'detail': 'Preparation request exceeds 16000 bytes'}, status_code=413)(scope, receive, send)
            messages.append(message)
            if not message.get('more_body', False):
                break
        index = 0
        async def replay():
            nonlocal index
            if index < len(messages):
                message = messages[index]; index += 1
                return message
            return await receive()
        return await self.app(scope, replay, send)


def physical_lab_router(service, owner_of, mutation_origin):
    router = APIRouter(prefix='/v1/physical-labs', tags=['physical-lab-preparation'])

    @router.get('/experiments')
    def experiments(request: Request):
        owner_of(request)
        return service.catalogue()

    @router.get('/experiments/{experiment_id}')
    def experiment(experiment_id: str, request: Request):
        owner_of(request)
        return service.pack(experiment_id)

    @router.get('/assets/{name}')
    def asset(name: str, request: Request):
        owner_of(request)
        # Retain versioned apparatus for sessions pinned before a visual update.
        if name not in {p.name for p in (ROOT / 'assets').glob('*.gltf')}:
            raise HTTPException(404, 'Apparatus asset not found')
        return FileResponse(ROOT / 'assets' / name, media_type='model/gltf+json',
                            headers={'Cache-Control': 'private, max-age=0, must-revalidate'})

    @router.get('/preview')
    def preview(request: Request):
        owner_of(request)
        return FileResponse(ROOT / 'static' / 'preview.html')

    @router.get('/preview.js')
    def preview_js(request: Request):
        owner_of(request)
        return FileResponse(ROOT / 'static' / 'preview.js', media_type='text/javascript')

    @router.get('/apparatus-viewer.mjs')
    def apparatus_viewer(request: Request):
        owner_of(request)
        return FileResponse(ROOT / 'static' / 'apparatus-viewer.mjs', media_type='text/javascript')

    @router.get('/preparation-client.mjs')
    def preparation_client(request: Request):
        owner_of(request)
        return FileResponse(ROOT / 'static' / 'preparation-client.mjs', media_type='text/javascript')

    @router.get('/component-hints.mjs')
    def component_hints(request: Request):
        owner_of(request)
        return FileResponse(ROOT / 'static' / 'component-hints.mjs', media_type='text/javascript')

    @router.post('/sessions', status_code=201)
    def create(request: Request, body: CreatePreparation, idempotency_key: str = Header(..., alias='Idempotency-Key')):
        owner = owner_of(request); mutation_origin(request)
        if not re.fullmatch(r'[A-Za-z0-9_.:-]{1,100}', idempotency_key):
            raise HTTPException(422, 'Invalid Idempotency-Key')
        return service.create(owner, idempotency_key, body)

    @router.get('/sessions')
    def sessions(request: Request):
        return service.list_sessions(owner_of(request))

    @router.get('/sessions/{session_id}')
    def session(session_id: str, request: Request):
        return service.get(session_id, owner_of(request))

    @router.get('/sessions/{session_id}/pack')
    def session_pack(session_id: str, request: Request):
        return service.session_pack(session_id, owner_of(request))

    @router.post('/sessions/{session_id}/events')
    def event(session_id: str, request: Request, body: PreparationEvent):
        owner = owner_of(request); mutation_origin(request)
        return service.event(session_id, owner, body)

    @router.get('/sessions/{session_id}/observations')
    def observations(session_id: str, request: Request):
        return service.observations(session_id, owner_of(request))

    @router.get('/sessions/{session_id}/receipt')
    def receipt(session_id: str, request: Request):
        return service.receipt(session_id, owner_of(request))

    @router.get('/sessions/{session_id}/experiment-result')
    def experiment_result(session_id: str, request: Request):
        return service.experiment_result(session_id, owner_of(request))

    return router
