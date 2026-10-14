"""Compose frozen screen/lab routes and mixed-language jobs in one FastAPI app."""
from contextlib import asynccontextmanager
import os
from pathlib import Path
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from contracts.lab_tracking import StartLab, AttachCapture, CheckFrame, ReviewCriteria, StudentResponse, ContextChange
from prototypes.screen_capture.server import create_app as screen_app, COOKIE, same_origin
from prototypes.mixed_language.service import MixedLanguageService
from prototypes.mixed_language.api import mixed_language_router, MixedBodyLimit

def create_app(data_dir=Path('work/backend'), *, analyzer=None, text_factory=None, speech_factory=None, proxy_secret=None):
    secret=os.environ.get('KIKI_PROXY_SECRET','') if proxy_secret is None else proxy_secret
    app=screen_app(data_dir,analyzer=analyzer,proxy_secret=secret)
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
    app.add_middleware(MixedBodyLimit)

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
