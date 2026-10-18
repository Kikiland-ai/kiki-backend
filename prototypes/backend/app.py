"""Compose frozen screen/lab routes and mixed-language jobs in one FastAPI app."""
from contextlib import asynccontextmanager
import os
from pathlib import Path
from fastapi import HTTPException,Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse,FileResponse
from fastapi.openapi.utils import get_openapi
from contracts.lab_tracking import StartLab, AttachCapture, CheckFrame, ReviewCriteria, StudentResponse, ContextChange
from prototypes.screen_capture.server import create_app as screen_app, COOKIE, same_origin
from prototypes.mixed_language.service import MixedLanguageService
from prototypes.mixed_language.api import mixed_language_router, MixedBodyLimit
from prototypes.json_stream.analysis import JsonStreamingAnalyzer
from prototypes.json_stream.api import stream_router
from prototypes.backend.lab_idempotency import LabCreateKeys, start_lab_route

def create_app(data_dir=Path('work/backend'), *, analyzer=None, text_factory=None, speech_factory=None, proxy_secret=None):
    secret=os.environ.get('KIKI_PROXY_SECRET','') if proxy_secret is None else proxy_secret
    app=screen_app(data_dir,analyzer=analyzer if analyzer is not None else JsonStreamingAnalyzer(),proxy_secret=secret)
    app.title='Kiki unified prototype API'; app.version='0.1.0'
    jobs=MixedLanguageService(data_dir,text_factory=text_factory,speech_factory=speech_factory)
    app.state.mixed_language=jobs

    def owner_of(request):
        owner=request.headers.get('x-kiki-owner') if secret else request.cookies.get(COOKIE)
        if not owner: raise HTTPException(401,'Open the application first')
        return owner

    def mutation_origin(request):
        if not same_origin(request.headers.get('origin'),request.headers.get('host')):
            raise HTTPException(403,'Same-origin request required')

    app.include_router(mixed_language_router(jobs,owner_of,mutation_origin))
    app.include_router(stream_router(app.state.lab,owner_of,mutation_origin))
    app.add_middleware(MixedBodyLimit)

    # Shadow the frozen create route (it sits inside an included router) so a trusted upstream
    # can safely retry it with Idempotency-Key. It must match first; the schema keeps the frozen operation.
    app.state.lab_keys=LabCreateKeys(Path(data_dir))
    app.add_api_route('/lab-sessions',start_lab_route(app.state.lab,app.state.lab_keys,owner_of,mutation_origin),
        methods=['POST'],status_code=201,include_in_schema=False)
    app.router.routes.insert(0,app.router.routes.pop())

    if getattr(app.state.lab.analyzer,'supports_stream',False):
        assets=Path(__file__).resolve().parents[1]/'json_stream_site'/'assets'
        root_route=next(route for route in app.routes if getattr(route,'path',None)=='/')
        original_page=root_route.endpoint;app.routes.remove(root_route)
        @app.get('/')
        async def stream_page(request:Request):
            previous=await original_page(request)
            return FileResponse(assets/'index.html',headers=dict(previous.headers))
        static_route=next(route for route in app.routes if getattr(route,'path',None)=='/static/{name}')
        original_asset=static_route.endpoint;app.routes.remove(static_route)
        @app.get('/static/{name}')
        async def stream_asset(name:str):
            if name in ('lab.js','json-stream-client.js'):return FileResponse(assets/name)
            # Python retains its native WebSocket capture transport.
            return await original_asset(name)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, error):
        return JSONResponse({'detail':'Invalid request fields'},status_code=422)

    # Extend the existing health route without altering the frozen screen app.
    original=next(route for route in app.routes if getattr(route,'path',None)=='/health')
    original_health=original.endpoint
    app.routes.remove(original)
    @app.get('/health',tags=['runtime'])
    async def health():
        value=await original_health()
        value['mode']='screen_lab_and_mixed_language_jobs'
        value['api_schema']='kiki-prototype-api/v1'
        value['latency_experiment']={'id':'stream-context-batch/v1','provider_io_mode':getattr(getattr(app.state.lab.analyzer,'provider',None),'io_mode',None),'context_validation_mode':os.environ.get('KIKI_STREAM_CONTEXT_MODE','per_chunk')}
        value['json_stream']={'available':bool(getattr(app.state.lab.analyzer,'supports_stream',False)),'wire_format':'lab-analysis-stream/v2','priority':['criteria','action_findings','uncertainties'],'commit_before_auxiliary':True}
        value['mixed_language']={'text_configured':jobs.text_configured,'speech_configured':jobs.speech_configured,
            'text_model':jobs.text_model,'speech_model':jobs.speech_model,'voice':jobs.voice,'workers':jobs.workers,
            'mode':jobs.mode,'key_rotation':False}
        return value

    # Existing lab transport performs bounded parsing itself. Publish its actual
    # Pydantic request contracts for frontend generation without changing semantics.
    lab_bodies={'/lab-sessions':StartLab, '/lab-sessions/{lab_id}/attach':AttachCapture,
        '/lab-sessions/{lab_id}/check':CheckFrame, '/lab-sessions/{lab_id}/review':ReviewCriteria,
        '/lab-sessions/{lab_id}/responses':StudentResponse, '/lab-sessions/{lab_id}/context':ContextChange}
    def openapi():
        if app.openapi_schema is not None: return app.openapi_schema
        schema=get_openapi(title=app.title,version=app.version,routes=app.routes)
        components=schema.setdefault('components',{}).setdefault('schemas',{})
        for path,model in lab_bodies.items():
            shape=model.model_json_schema(ref_template='#/components/schemas/{model}')
            components.update(shape.pop('$defs',{})); components[model.__name__]=shape
            schema['paths'][path]['post']['requestBody']={'required':True,'content':{'application/json':{'schema':{'$ref':'#/components/schemas/'+model.__name__}}}}
        schema['paths']['/lab-sessions']['post']['parameters']=[{'name':'Idempotency-Key','in':'header','required':False,
            'description':'Optional. The same owner, key and body return the lab created first; the same key with a different body is 409.',
            'schema':{'type':'string','pattern':'^[A-Za-z0-9_.:-]{1,100}$'}}]
        components['SafeValidationError']={'type':'object','properties':{'detail':{'type':'string'}},'required':['detail']}
        for path in schema['paths'].values():
            for operation in path.values():
                if isinstance(operation,dict) and 'responses' in operation and '422' in operation['responses']:
                    operation['responses']['422']={'description':'Invalid request fields; submitted source is never echoed','content':{'application/json':{'schema':{'$ref':'#/components/schemas/SafeValidationError'}}}}
        app.openapi_schema=schema
        return schema
    app.openapi=openapi

    old_lifespan=app.router.lifespan_context
    @asynccontextmanager
    async def lifespan(application):
        async with old_lifespan(application):
            await jobs.start()
            try: yield
            finally: await jobs.stop()
    app.router.lifespan_context=lifespan
    return app
