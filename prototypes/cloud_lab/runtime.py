"""IAM-private Cloud Run lab engine. No SQLite, executor or generation jobs."""
import asyncio
import json
import os
import re
import time
import uuid

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from pydantic import ValidationError

from contracts.screen_capture import FrameEnvelope
from prototypes.backend.lab_idempotency import start_lab_route
from prototypes.json_stream.analysis import JsonStreamingAnalyzer
from prototypes.json_stream.api import stream_router
from prototypes.lab_tracking.api import lab_router
from prototypes.screen_capture.cloud_access import SiteProxyGuard
from prototypes.screen_capture.server import same_origin, validate_image
from .capture import FirestoreCaptureStore
from .domain import CloudLabService
from .frames import FirestoreImages, CheckedFrameWriteGuard
from .provider_state import FirestoreStreamingProviderPool
from .store import FirestoreLabStore, CloudLabCreateKeys
from .telemetry import ATTEMPT_CONTEXT


class CloudAnalyzer(JsonStreamingAnalyzer):
    async def analyze(self, pixels, checkpoint, state):
        token = ATTEMPT_CONTEXT.set({'lab_session_id': state['lab_session_id'], 'lab_revision': state['revision'], 'checkpoint_id': checkpoint['id']})
        try:
            return await super().analyze(pixels, checkpoint, state)
        finally:
            ATTEMPT_CONTEXT.reset(token)


def create_app(*, client=None, analyzer=None, proxy_secret=None, clock=time.time, collection_prefix='kiki_cloud'):
    trial_value = os.environ.get('KIKI_TRIAL_MAX_CHECKS')
    trial_limit = None
    if trial_value is not None:
        if not re.fullmatch(r'[1-9][0-9]{0,3}', trial_value) or int(trial_value) > 1000:
            raise RuntimeError('KIKI_TRIAL_MAX_CHECKS must be an integer from 1 to 1000')
        trial_limit = int(trial_value)
    secret = os.environ.get('KIKI_PROXY_SECRET', '') if proxy_secret is None else proxy_secret
    if len(secret) < 32:
        raise RuntimeError('Cloud lab requires the managed proxy secret')
    if client is None:
        project = os.environ.get('KIKI_GCP_PROJECT') or os.environ.get('GOOGLE_CLOUD_PROJECT')
        database = os.environ.get('KIKI_FIRESTORE_DATABASE', '')
        if not project or not database or database == '(default)':
            raise RuntimeError('Cloud lab requires explicit project and named Firestore database')
        from google.cloud import firestore
        client = firestore.Client(project=project, database=database)
    captures = FirestoreCaptureStore(client, collection_prefix, clock=clock)
    store = FirestoreLabStore(client, collection_prefix, clock=clock)
    images = FirestoreImages(client, collection_prefix=collection_prefix+'_checked', clock=clock,
                             write_guard=CheckedFrameWriteGuard(client, collection_prefix, clock=clock))
    if analyzer is None:
        analyzer = CloudAnalyzer()
        analyzer.provider = FirestoreStreamingProviderPool(client, collection_prefix=collection_prefix, clock=clock)
    lab = CloudLabService(store, captures.capture_access, analyzer, images=images, clock=clock,
                          capture_status=lambda sid, owner: {"status": captures.session(sid, owner)["status"]},
                          capture_snapshot=store.capture_snapshot, trial_check_limit=trial_limit)
    app = FastAPI(title='Kiki cloud lab engine', version='1.0.0')
    app.state.store, app.state.lab, app.state.captures = store, lab, captures
    app.state.lab_keys = CloudLabCreateKeys(store)

    def owner_of(request):
        owner = request.headers.get('x-kiki-owner')
        if not owner or len(owner) > 256:
            raise HTTPException(401, 'Authenticated application required')
        return owner

    def mutation_origin(request):
        if not same_origin(request.headers.get('origin'), request.headers.get('host')):
            raise HTTPException(403, 'Same-origin request required')

    @app.middleware('http')
    async def headers(request, call_next):
        response = await call_next(request)
        response.headers.update({'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'same-origin'})
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid(request, error):
        return JSONResponse({'detail': 'Invalid request fields'}, status_code=422)

    @app.get('/health')
    async def health():
        return {'status': 'ok', 'mode': 'cloud_screen_lab', 'api_schema': 'kiki-prototype-api/v1',
                'trial_check_limit': lab.trial_check_limit,
                'lab_storage': 'named_firestore', 'image_storage': 'private_latest_firestore_chunks_30s_access_ttl',
                'analysis': {'provider': 'gemini', 'configured': analyzer.configured, 'model': getattr(analyzer, 'model', None)},
                'json_stream': {'available': bool(getattr(analyzer, 'supports_stream', False)), 'wire_format': 'lab-analysis-stream/v2'},
                'mixed_language': {'available': False, 'reason': 'prepared_media_only_cloud_runtime'}}

    # Place keyed create before the frozen router's unkeyed route.
    app.add_api_route('/lab-sessions', start_lab_route(lab, app.state.lab_keys, owner_of, mutation_origin), methods=['POST'], status_code=201)
    app.include_router(lab_router(lab, owner_of, mutation_origin))
    app.include_router(stream_router(lab, owner_of, mutation_origin))

    @app.post('/screen-sessions', status_code=201)
    async def create_capture(request: Request):
        mutation_origin(request)
        session_id = captures.create(owner_of(request))
        return {'session_id': session_id, 'stream_path': f'/screen-sessions/{session_id}/stream',
                'sample_interval_ms': 2000, 'max_frame_bytes': 1000000, 'session_limit_seconds': None}

    @app.get('/screen-sessions/{session_id}/observation')
    async def observation(session_id: str, request: Request):
        return captures.snapshot(captures.session(session_id, owner_of(request)))

    @app.get('/screen-sessions/{session_id}/frame')
    async def image(session_id: str, request: Request):
        value = captures.capture_access(session_id, owner_of(request))
        if value['pixels'] is None:
            raise HTTPException(410, 'Fresh shared frame unavailable; start a new share')
        return Response(value['pixels'], media_type='image/jpeg', headers={'X-Frame-Sequence': str(value['frame']['sequence'])})

    @app.get('/screen-sessions/{session_id}/events')
    async def events(session_id: str, request: Request, after: int = 0, limit: int = 100):
        if after < 0 or not 1 <= limit <= 100:
            raise HTTPException(422, 'Invalid event cursor or limit')
        items = captures.events(session_id, owner_of(request), after, limit)
        return {'events': items, 'next_cursor': items[-1]['sequence'] if items else after}

    @app.post('/screen-sessions/{session_id}/stop')
    async def stop(session_id: str, request: Request):
        mutation_origin(request)
        row = captures.set_status(session_id, owner_of(request), 'ended', 'capture_stopped')
        lab.capture_changed(session_id, 'ended')
        return captures.snapshot(row)

    @app.websocket('/screen-sessions/{session_id}/stream')
    async def stream(ws: WebSocket, session_id: str):
        if not same_origin(ws.headers.get('origin'), ws.headers.get('host')):
            await ws.close(code=1008)
            return
        producer, fence, owner = uuid.uuid4().hex, None, None
        try:
            owner = owner_of(ws)
            row = captures.acquire_producer(session_id, owner, producer)
            fence = row['fence']
        except HTTPException:
            await ws.close(code=1008)
            return
        await ws.accept()
        try:
            # Replacement never silently restores a previously admitted candidate.
            lab.capture_changed(session_id, 'disconnected')
            await ws.send_json({'type': 'connected', 'observation': captures.snapshot(row)})
            while True:
                message = await asyncio.wait_for(ws.receive(), 20)
                if message['type'] == 'websocket.disconnect':
                    break
                text = message.get('text')
                if text is None or len(text.encode()) > 4096:
                    raise ValueError('Expected bounded metadata')
                body = json.loads(text)
                if not isinstance(body, dict):
                    raise ValueError('Expected object')
                row = captures.renew(session_id, owner, producer, fence)
                kind = body.get('type')
                if kind == 'heartbeat':
                    await ws.send_json({'type': 'heartbeat', 'observation': captures.snapshot(row)})
                    continue
                if kind in ('capture_started', 'pause', 'resume', 'stop'):
                    if ((kind == 'resume' and row['status'] != 'paused')
                            or (kind == 'pause' and row['status'] != 'sharing')
                            or (kind == 'capture_started' and row['status'] != 'awaiting_share')):
                        raise ValueError('A fresh Share is required')
                    desired = {'capture_started': 'sharing', 'pause': 'paused', 'resume': 'sharing', 'stop': 'ended'}[kind]
                    row = captures.set_status(session_id, owner, desired, kind, producer=producer, fence=fence)
                    lab.capture_changed(session_id, desired)
                    await ws.send_json({'type': 'status', 'observation': captures.snapshot(row)})
                    if kind == 'stop':
                        break
                    continue
                meta = FrameEnvelope.model_validate(body)
                binary = await asyncio.wait_for(ws.receive(), 5)
                payload = binary.get('bytes')
                if payload is None or len(payload) > 1000000:
                    raise ValueError('Expected JPEG bytes')
                await asyncio.to_thread(validate_image, payload, meta)
                duplicate, row = captures.frame(session_id, owner, producer, fence, meta.model_dump(exclude={'type'}), payload)
                if duplicate is None:
                    await ws.send_json({'type': 'skipped', 'reason': 'sampling_limit'})
                else:
                    lab.capture_changed(session_id, 'sharing', meta.view_revision)
                    await ws.send_json({'type': 'ack', 'duplicate': duplicate, 'observation': captures.snapshot(row)})
        except WebSocketDisconnect:
            pass
        except (ValueError, ValidationError, asyncio.TimeoutError, HTTPException):
            try:
                await ws.send_json({'type': 'error', 'message': 'Capture rejected or expired; start a new share.'})
            except (WebSocketDisconnect, RuntimeError):
                pass
        finally:
            released = captures.release(session_id, owner, producer, fence)
            if released is not None:
                lab.capture_changed(session_id, 'disconnected')
            try:
                await ws.close()
            except RuntimeError:
                pass

    app.add_middleware(SiteProxyGuard, secret=secret)
    return app
