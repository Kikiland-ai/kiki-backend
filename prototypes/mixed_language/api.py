"""Owner-scoped job transport; source and errors never enter validation logs."""
import re
from fastapi import APIRouter, Body, Header, HTTPException, Request
from fastapi.responses import Response
from contracts.mixed_language import CreateMixedLanguageJob, MixedLanguageJob, MixedLanguageResult

class MixedBodyLimit:
    def __init__(self, app): self.app=app
    async def __call__(self, scope, receive, send):
        if scope['type']!='http' or not scope['path'].startswith('/v1/mixed-language-jobs'):
            return await self.app(scope,receive,send)
        chunks=[]; size=0
        while True:
            message=await receive()
            if message['type']!='http.request': return
            size+=len(message.get('body',b''))
            if size>64000:
                from starlette.responses import JSONResponse
                return await JSONResponse({'detail':'Mixed-language request exceeds 64000 bytes'},status_code=413)(scope,receive,send)
            chunks.append(message)
            if not message.get('more_body',False): break
        index=0
        async def replay():
            nonlocal index
            if index<len(chunks):
                message=chunks[index]; index+=1; return message
            return await receive()
        return await self.app(scope,replay,send)

def mixed_language_router(service, owner_of, mutation_origin):
    router=APIRouter(prefix='/v1/mixed-language-jobs',tags=['mixed-language'])

    @router.post('', status_code=202, response_model=MixedLanguageJob)
    async def create(request: Request, body: CreateMixedLanguageJob=Body(...), idempotency_key: str=Header(...,alias='Idempotency-Key')):
        owner=owner_of(request); mutation_origin(request)
        if not re.fullmatch(r'[A-Za-z0-9_.:-]{1,100}',idempotency_key):
            raise HTTPException(422,'Idempotency-Key must be 1–100 ASCII identifier characters')
        return service.create(owner,idempotency_key,body)

    @router.get('/{job_id}',response_model=MixedLanguageJob)
    async def read(job_id: str, request: Request):
        return service.project(service.get(job_id,owner_of(request)))

    @router.get('/{job_id}/result',response_model=MixedLanguageResult)
    async def result(job_id: str, request: Request):
        return service.result(job_id,owner_of(request))

    @router.get('/{job_id}/audio')
    async def audio(job_id: str, request: Request):
        return Response(service.audio(job_id,owner_of(request)),media_type='audio/wav',headers={'Content-Disposition':'inline; filename="speech.wav"'})

    @router.post('/{job_id}/retry',response_model=MixedLanguageJob)
    async def retry(job_id: str, request: Request):
        owner=owner_of(request); mutation_origin(request)
        return service.retry(job_id,owner)

    @router.post('/{job_id}/cancel',response_model=MixedLanguageJob)
    async def cancel(job_id: str, request: Request):
        owner=owner_of(request); mutation_origin(request)
        return service.cancel(job_id,owner)

    return router
