"""Single-process durable queue; blocking legacy adapters run in bounded threads."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import uuid

from fastapi import HTTPException
from prototypes.mixed_script.pipeline import (GeminiGenerator, PipelineError, PROMPT_VERSION,
    digest, make_request, validate_input, validate_stage)
from prototypes.mixed_script.speech import GeminiSpeechGenerator, inspect_wav

PROFILE_VERSION = 'mixed-language-profile/v1'
TERMINAL = {'ready', 'failed', 'cancelled'}

def timestamp():
    return datetime.now(timezone.utc).isoformat()

def stage_request(source, stage, profile, translation=None):
    request = make_request(source, stage, translation)
    data = json.loads(request['contents'][0]['parts'][0]['text'])
    data['learner_language_profile'] = profile
    request['contents'][0]['parts'][0]['text'] = json.dumps(data, ensure_ascii=False)
    request['systemInstruction']['parts'][0]['text'] += '\nLearner-selected English and Odia ratings are style preferences, not assessed ability, technical understanding or word percentages. Use the supplied ratings to adjust clause complexity, while keeping Odia-led grammar, protected English terms and every original claim. Never omit ideas or add explanations to simplify the source.'
    return request

class MixedLanguageService:
    def __init__(self, directory, *, text_factory=None, speech_factory=None, workers=2):
        directory = Path(directory); directory.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(directory / 'mixed-language.sqlite', check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript('''PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS mixed_jobs (
            id TEXT PRIMARY KEY, owner TEXT NOT NULL, idem TEXT NOT NULL,
            request_hash TEXT NOT NULL, body TEXT NOT NULL, audio BLOB,
            status TEXT NOT NULL,
            UNIQUE(owner, idem));
        CREATE INDEX IF NOT EXISTS mixed_jobs_status ON mixed_jobs(status);''')
        self.text_model = os.environ.get('GEMINI_TEXT_MODEL', 'gemini-3.5-flash-lite')
        self.speech_model = os.environ.get('GEMINI_SPEECH_MODEL', 'gemini-3.8-flash-lite-tts')
        self.voice = os.environ.get('GEMINI_SPEECH_VOICE', 'Kore')
        self.key = os.environ.get('GEMINI_API_KEY', '')
        self.text_factory = text_factory or (lambda: GeminiGenerator(self.key, model=self.text_model, timeout=60))
        self.speech_factory = speech_factory or (lambda: GeminiSpeechGenerator(self.key, model=self.speech_model, voice=self.voice, timeout=180))
        self.text_configured = text_factory is not None or bool(self.key.strip())
        self.speech_configured = speech_factory is not None or bool(self.key.strip())
        self.mode = 'injected_test_adapter' if text_factory else 'gemini'
        self.workers = workers
        self.executor = ThreadPoolExecutor(max_workers=workers, thread_name_prefix='mixed-language')
        self.tasks = set(); self.dispatcher = None; self.closed = False
        # Interrupted provider work may already have cost money. Require explicit retry.
        for row in self.db.execute("SELECT * FROM mixed_jobs WHERE status NOT IN ('ready','failed','cancelled','queued')").fetchall():
            state = json.loads(row['body'])
            if state['status'] not in TERMINAL | {'queued'}:
                state['generation'] += 1
                state['status'] = 'failed'; state['error'] = {'category':'worker_interrupted', 'retry_allowed':True}
                for stage in state['stages'].values():
                    if stage['status'] == 'running': stage['status'] = 'failed'
                self._save(state)

    def _save(self, state, audio=None):
        state['revision'] += 1; state['updated_at'] = timestamp()
        with self.db:
            self.db.execute('UPDATE mixed_jobs SET body=?,status=? WHERE id=?', (json.dumps(state, ensure_ascii=False), state['status'],state['job_id']))
            if audio is not None:
                self.db.execute('UPDATE mixed_jobs SET audio=? WHERE id=?', (audio, state['job_id']))

    def get(self, job_id, owner):
        row = self.db.execute('SELECT body FROM mixed_jobs WHERE id=? AND owner=?', (job_id, owner)).fetchone()
        if row is None: raise HTTPException(404, 'Job not found')
        return json.loads(row['body'])

    def _current(self, job_id, generation):
        row = self.db.execute('SELECT body FROM mixed_jobs WHERE id=?', (job_id,)).fetchone()
        state = json.loads(row['body']) if row else None
        return state if state and state['generation'] == generation and state['status'] not in TERMINAL else None

    @staticmethod
    def project(state):
        base = '/v1/mixed-language-jobs/' + state['job_id']
        return {'schema':'mixed-language-job/v1', **{k:state[k] for k in ('job_id','revision','status','created_at','updated_at','profile','attempts','error')},
            'stages':{k:{'status':v['status']} for k,v in state['stages'].items()},
            'source_id':state['request']['source']['id'], 'source_sha256':digest(state['request']['source']),
            'text_ready':state['stages']['mixed']['status']=='ready',
            'audio_ready':state['stages']['audio']['status']=='ready',
            'provenance':{'mode':state['mode'],'text_model':state['text_model'],'speech_model':state['speech_model'], 'prompt_version':PROMPT_VERSION,'profile_policy_version':PROFILE_VERSION},
            'review':{'meaning':'pending','native_Odia':'pending','pronunciation':'pending','alignment':'not_performed'},
            'links':{'status':base,'result':base+'/result','audio':base+'/audio' if state['stages']['audio']['status']=='ready' else None,'retry':base+'/retry','cancel':base+'/cancel'}}

    def create(self, owner, idem, request):
        payload = request.model_dump(); request_hash = digest(payload)
        old = self.db.execute('SELECT body,request_hash FROM mixed_jobs WHERE owner=? AND idem=?', (owner, idem)).fetchone()
        if old:
            if old['request_hash'] != request_hash: raise HTTPException(409, 'Idempotency key already used for a different request')
            return self.project(json.loads(old['body']))
        try: validate_input(payload['source'])
        except PipelineError: raise HTTPException(422, 'Invalid prepared mixed-script-input/v1 source') from None
        if not self.text_configured or (payload['audio']['enabled'] and not self.speech_configured):
            raise HTTPException(503, 'Mixed-language provider is not configured')
        state = {'job_id':str(uuid.uuid4()),'revision':1,'generation':0,'status':'queued',
            'created_at':timestamp(),'updated_at':timestamp(),'request':payload,'profile':payload['profile'],
            'mode':self.mode,'text_model':self.text_model,'speech_model':self.speech_model,'voice':self.voice,
            'attempts':0,'error':None,'stages':{s:{'status':'pending','output':None} for s in ('translation','mixed','audio')}, 'calls':[]}
        if not payload['audio']['enabled']: state['stages']['audio']['status'] = 'disabled'
        with self.db:
            self.db.execute('INSERT INTO mixed_jobs(id,owner,idem,request_hash,body,status) VALUES(?,?,?,?,?,?)', (state['job_id'],owner,idem,request_hash,json.dumps(state,ensure_ascii=False),state['status']))
        return self.project(state)

    def cancel(self, job_id, owner):
        state = self.get(job_id, owner)
        if state['status'] in {'ready','cancelled'}: return self.project(state)
        state['generation'] += 1; state['status'] = 'cancelled'; state['error'] = None
        for stage in state['stages'].values():
            if stage['status'] in {'pending','running','failed'}: stage['status']='cancelled'
        self._save(state)
        return self.project(state)

    def retry(self, job_id, owner):
        state = self.get(job_id, owner)
        if state['status'] != 'failed': raise HTTPException(409, 'Only a failed job can be retried')
        if state['text_model'] != self.text_model or state['speech_model'] != self.speech_model or state['voice'] != self.voice:
            raise HTTPException(409, 'Server model policy changed; create a new job deliberately')
        if state['attempts'] >= 3: raise HTTPException(409, 'Prototype retry budget exhausted; create a new job deliberately')
        state['generation'] += 1; state['status'] = 'queued'; state['error'] = None
        for stage in state['stages'].values():
            if stage['status'] in {'running','failed'}: stage['status'] = 'pending'
        self._save(state)
        return self.project(state)

    def result(self, job_id, owner):
        state = self.get(job_id, owner)
        if state['stages']['mixed']['status'] != 'ready': raise HTTPException(409, 'Validated mixed text is not ready')
        mixed = state['stages']['mixed']['output']
        return {'schema':'mixed-language-result/v1','job_id':job_id,'source':state['request']['source'],'profile':state['profile'],
            'translation':state['stages']['translation']['output'],'mixed':mixed,
            'paragraph':' '.join(s['display_text'] for s in mixed['sentences']),
            'speech_script':' '.join(s['speech_text'] for s in mixed['sentences']),
            'validation':{'automated':'passed','meaning_review':'pending','native_Odia_review':'pending'},
            'provenance':{**self.project(state)['provenance'],'calls':state['calls']},
            'audio':{'status':state['stages']['audio']['status'],'manifest':state['stages']['audio']['output'], 'url':self.project(state)['links']['audio'],'timing_cues':None}}

    def audio(self, job_id, owner):
        state = self.get(job_id, owner)
        if state['stages']['audio']['status'] != 'ready': raise HTTPException(409, 'Audio is not ready')
        row = self.db.execute('SELECT audio FROM mixed_jobs WHERE id=? AND owner=?',(job_id,owner)).fetchone()
        return bytes(row['audio'])

    async def _blocking(self, function, *args):
        return await asyncio.get_running_loop().run_in_executor(self.executor, function, *args)

    async def run(self, job_id):
        row = self.db.execute('SELECT body FROM mixed_jobs WHERE id=?', (job_id,)).fetchone()
        state = json.loads(row['body'])
        if state['status'] != 'queued': return
        state['generation'] += 1; state['attempts'] += 1; generation=state['generation']
        state['status'] = 'translating'; self._save(state)
        stage = 'translation'
        try:
            source=state['request']['source']; glossary=validate_input(source)
            generator=None
            for stage, status in [('translation','translating'),('mixed','refining')]:
                state=self._current(job_id,generation)
                if state is None: return
                if state['stages'][stage]['status']=='ready': continue
                state['status']=status; state['stages'][stage]['status']='running'; self._save(state)
                if generator is None: generator=self.text_factory()
                request=stage_request(source,stage,state['profile'],state['stages']['translation']['output'] if stage=='mixed' else None)
                value=await self._blocking(generator.generate,stage,request)
                output=validate_stage(source,value,glossary)
                state=self._current(job_id,generation)
                if state is None: return
                state['stages'][stage]={'status':'ready','output':output}
                state['calls'].append({'stage':stage,'request_sha256':digest(request),'mode':state['mode'],'model':state['text_model'], 'adapter_call':generator.calls[-1] if generator.calls else None})
                if stage=='mixed': state['status']='text_ready'
                self._save(state)
            state=self._current(job_id,generation)
            if state is None: return
            if state['stages']['audio']['status']=='disabled':
                state['status']='ready'; self._save(state); return
            stage='audio'; state['status']='synthesizing'; state['stages']['audio']['status']='running'; self._save(state)
            transcript=' '.join(s['speech_text'] for s in state['stages']['mixed']['output']['sentences'])
            speech=self.speech_factory()
            audio,manifest=await self._blocking(speech.generate,transcript)
            metrics=await self._blocking(inspect_wav,audio)
            if manifest.get('audio',{}).get('sha256') != metrics['sha256'] or manifest.get('speech_script_sha256') != hashlib.sha256(transcript.encode()).hexdigest():
                raise PipelineError('Audio provenance mismatch')
            state=self._current(job_id,generation)
            if state is None: return
            state['stages']['audio']={'status':'ready','output':manifest}; state['status']='ready'; self._save(state,audio)
        except asyncio.CancelledError:
            raise
        except Exception as error:
            state=self._current(job_id,generation)
            if state is not None:
                state['status']='failed'; state['stages'][stage]['status']='failed'
                # No arbitrary exception/provider body or source text is exposed.
                state['error']={'category':'pipeline_failure' if isinstance(error,PipelineError) else 'worker_failure','failed_stage':stage,'retry_allowed':state['attempts']<3}
                self._save(state)

    async def dispatch(self):
        while not self.closed:
            free=self.workers-len(self.tasks)
            if free>0:
                for row in self.db.execute("SELECT id FROM mixed_jobs WHERE status='queued' ORDER BY rowid LIMIT ?",(free,)).fetchall():
                    if free<=0: break
                    task=asyncio.create_task(self.run(row['id'])); self.tasks.add(task); task.add_done_callback(self.tasks.discard); free-=1
            await asyncio.sleep(0.1)

    async def start(self):
        self.dispatcher=asyncio.create_task(self.dispatch())

    async def stop(self):
        self.closed=True
        if self.dispatcher: self.dispatcher.cancel()
        tasks=list(self.tasks)
        for task in tasks: task.cancel()
        await asyncio.gather(*tasks, *([self.dispatcher] if self.dispatcher else []), return_exceptions=True)
        for row in self.db.execute("SELECT body FROM mixed_jobs WHERE status NOT IN ('ready','failed','cancelled','queued')").fetchall():
            state=json.loads(row['body'])
            if state['status'] not in TERMINAL | {'queued'}:
                state['generation']+=1; state['status']='failed'; state['error']={'category':'worker_interrupted','retry_allowed':state['attempts']<3}
                for item in state['stages'].values():
                    if item['status']=='running': item['status']='failed'
                self._save(state)
        self.executor.shutdown(wait=False,cancel_futures=True)
        self.db.close()
