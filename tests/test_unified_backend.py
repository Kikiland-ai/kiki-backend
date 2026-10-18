"""Offline API/job acceptance: durability, ownership, readiness and late-result fences."""
import asyncio
import copy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
import wave
from fastapi.testclient import TestClient
from contracts.mixed_language import CreateMixedLanguageJob
from prototypes.backend.app import create_app
from prototypes.mixed_language.service import MixedLanguageService
from prototypes.mixed_script.pipeline import DEFAULT_INPUT,DEFAULT_FIXTURE,read_json,FixtureGenerator,PipelineError
from prototypes.mixed_script.speech import inspect_wav

class SpeechFixture:
    model='fixture-speech'
    def __init__(self, gate=None, fail=False): self.gate=gate; self.fail=fail; self.calls=0
    def generate(self, transcript):
        self.calls+=1
        if self.gate: self.gate.wait(5)
        if self.fail: raise PipelineError('controlled failure')
        stream=io.BytesIO()
        with wave.open(stream,'wb') as wav:
            wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(24000)
            wav.writeframes(b'\x01\x00'*2400)
        data=stream.getvalue()
        return data,{'audio':inspect_wav(data),'speech_script_sha256':hashlib.sha256(transcript.encode()).hexdigest(),'timing_cues':None}

class UnifiedBackendTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.directory=Path(self.temp.name)
        self.fixture=read_json(DEFAULT_FIXTURE)
        self.source=read_json(DEFAULT_INPUT)
        self.body={'source':self.source,'profile':{'english_proficiency':5,'odia_proficiency':7},'audio':{'enabled':False}}
        self.generated=[]
        def text_factory():
            g=FixtureGenerator(self.fixture); self.generated.append(g); return g
        self.factory=text_factory; self.speech=SpeechFixture()
        self.app=create_app(self.directory,text_factory=self.factory,speech_factory=lambda:self.speech,proxy_secret='')
        self.client=TestClient(self.app); self.client.__enter__(); self.client.get('/')
        self.headers={'origin':'http://testserver','Idempotency-Key':'test-1'}
    def tearDown(self):
        if self.speech.gate:self.speech.gate.set()
        self.client.__exit__(None,None,None)
        self.app.state.store.db.close(); self.app.state.lab.store.db.close(); self.app.state.lab_keys.db.close(); self.temp.cleanup()
    def submit(self, body=None, idem='test-1'):
        response=self.client.post('/v1/mixed-language-jobs',json=body or self.body,headers={**self.headers,'Idempotency-Key':idem})
        self.assertEqual(response.status_code,202,response.text); return response.json()
    def wait(self,job_id, predicate):
        until=time.monotonic()+3
        while time.monotonic()<until:
            state=self.client.get('/v1/mixed-language-jobs/'+job_id).json()
            if predicate(state):return state
            time.sleep(.01)
        self.fail('Job did not reach expected state: '+str(state))
    def test_one_app_exposes_screen_lab_and_prepared_source_job_openapi(self):
        health=self.client.get('/health').json(); self.assertEqual(health['backend'],'python_fastapi')
        paths=self.client.get('/openapi.json').json()['paths']
        self.assertIn('/screen-sessions',paths); self.assertIn('/lab-sessions/{lab_id}/check',paths)
        schema=paths['/v1/mixed-language-jobs']['post']['requestBody']; self.assertIn('content',schema)
        self.assertEqual(self.client.post('/lab-sessions',json={'model_name':'test','operator_trial':True},headers=self.headers).status_code,201)
        self.assertEqual(self.client.post('/screen-sessions',headers=self.headers).status_code,201)
    def test_idempotency_is_owner_scoped_and_body_bound(self):
        job=self.submit(); again=self.submit(); self.assertEqual(job['job_id'],again['job_id'])
        changed=copy.deepcopy(self.body); changed['profile']['english_proficiency']=4
        self.assertEqual(self.client.post('/v1/mixed-language-jobs',json=changed,headers=self.headers).status_code,409)
        stranger=TestClient(self.app); stranger.get('/')
        self.assertEqual(stranger.get(job['links']['status']).status_code,404)
        other=stranger.post('/v1/mixed-language-jobs',json=self.body,headers=self.headers)
        self.assertEqual(other.status_code,202); self.assertNotEqual(other.json()['job_id'],job['job_id']); stranger.close()
    def test_request_limits_profile_strictness_and_same_origin(self):
        bad=copy.deepcopy(self.body); bad['profile']['english_proficiency']='5'
        r=self.client.post('/v1/mixed-language-jobs',json=bad,headers=self.headers)
        self.assertEqual(r.status_code,422); self.assertNotIn('VCO',r.text)
        bad['profile']['english_proficiency']=True
        self.assertEqual(self.client.post('/v1/mixed-language-jobs',json=bad,headers=self.headers).status_code,422)
        self.assertEqual(self.client.post('/v1/mixed-language-jobs',json=self.body,headers={**self.headers,'origin':'https://foreign'}).status_code,403)
        r=self.client.post('/v1/mixed-language-jobs',content=b'x'*64001,headers={**self.headers,'Content-Type':'application/json'})
        self.assertEqual(r.status_code,413)
    def test_text_ready_before_audio_and_wav_is_separately_authorized(self):
        self.speech.gate=threading.Event(); body=copy.deepcopy(self.body);body['audio']['enabled']=True
        job=self.submit(body);state=self.wait(job['job_id'],lambda s:s['status']=='synthesizing')
        self.assertTrue(state['text_ready']); self.assertFalse(state['audio_ready'])
        result=self.client.get(job['links']['result']).json();self.assertEqual(result['audio']['status'],'running')
        self.assertIsNone(result['audio']['timing_cues']);self.assertEqual(result['validation']['meaning_review'],'pending')
        self.assertEqual(self.client.get(job['links']['status']+'/audio').status_code,409)
        self.speech.gate.set();state=self.wait(job['job_id'],lambda s:s['status']=='ready')
        r=self.client.get(state['links']['audio']);self.assertEqual(r.headers['content-type'],'audio/wav')
        self.assertGreater(inspect_wav(r.content)['duration_seconds'],0)
        stranger=TestClient(self.app);stranger.get('/')
        self.assertEqual(stranger.get(state['links']['audio']).status_code,404); stranger.close()
    def test_audio_failure_retry_keeps_validated_text_and_skips_text_calls(self):
        self.speech.fail=True;body=copy.deepcopy(self.body);body['audio']['enabled']=True
        job=self.submit(body);state=self.wait(job['job_id'],lambda s:s['status']=='failed')
        self.assertTrue(state['text_ready']);self.assertEqual(state['error']['failed_stage'],'audio')
        self.assertEqual(len(self.generated),1);self.assertEqual(len(self.generated[0].calls),2)
        self.speech.fail=False
        r=self.client.post(job['links']['retry'],headers=self.headers);self.assertEqual(r.status_code,200)
        state=self.wait(job['job_id'],lambda s:s['status']=='ready')
        self.assertEqual(len(self.generated),1);self.assertEqual(self.speech.calls,2)
        self.assertEqual(state['attempts'],2)
    def test_cancel_fences_late_audio_and_preserves_text_without_publishing_asset(self):
        self.speech.gate=threading.Event();body=copy.deepcopy(self.body);body['audio']['enabled']=True
        job=self.submit(body);self.wait(job['job_id'],lambda s:s['status']=='synthesizing')
        self.assertEqual(self.client.post(job['links']['cancel'],headers=self.headers).json()['status'],'cancelled')
        self.speech.gate.set();time.sleep(.05)
        state=self.client.get(job['links']['status']).json();self.assertEqual(state['status'],'cancelled')
        self.assertTrue(state['text_ready']);self.assertFalse(state['audio_ready'])
        self.assertEqual(self.client.get(job['links']['status']+'/audio').status_code,409)
        self.assertEqual(self.client.post(job['links']['retry'],headers=self.headers).status_code,409)
    def test_profile_is_snapshotted_in_model_request_and_no_lab_progress_is_changed(self):
        from prototypes.mixed_language.service import stage_request
        request=stage_request(self.source,'translation',self.body['profile'])
        context=json.loads(request['contents'][0]['parts'][0]['text'])
        self.assertEqual(context['learner_language_profile'],self.body['profile']);self.assertEqual(context['original'],self.source)
        job=self.submit();self.wait(job['job_id'],lambda s:s['status']=='ready')
        self.assertEqual(self.client.get('/lab-sessions').json(),[])
    def test_restart_requires_explicit_retry_and_reuses_completed_translation(self):
        directory=self.directory/'restart';g=FixtureGenerator(self.fixture)
        service=MixedLanguageService(directory,text_factory=lambda:g)
        job=service.create('owner','restart',CreateMixedLanguageJob.model_validate(self.body))
        state=service.get(job['job_id'],'owner')
        from prototypes.mixed_script.pipeline import validate_input,validate_stage
        state['stages']['translation']={'status':'ready','output':validate_stage(self.source,self.fixture['translation'],validate_input(self.source))}
        state['stages']['mixed']['status']='running';state['status']='refining';state['attempts']=1;service._save(state)
        service.executor.shutdown(wait=False);service.db.close()
        g2=FixtureGenerator(self.fixture);restart=MixedLanguageService(directory,text_factory=lambda:g2)
        state=restart.get(job['job_id'],'owner');self.assertEqual(state['status'],'failed')
        self.assertEqual(state['error']['category'],'worker_interrupted')
        restart.retry(job['job_id'],'owner');asyncio.run(restart.run(job['job_id']))
        self.assertEqual([c['stage'] for c in g2.calls],['mixed'])
        self.assertEqual(restart.get(job['job_id'],'owner')['status'],'ready')
        restart.executor.shutdown(wait=False);restart.db.close()
    def test_lab_creation_replays_an_idempotency_key_for_the_same_owner_and_body(self):
        secret='controlled-proxy-secret-at-least-32-characters'
        directory=self.directory/'idempotent'
        alice={'x-kiki-proxy-key':secret,'x-kiki-owner':'fb:alice-uid','origin':'http://testserver'}
        body={'operator_trial':True,'model_name':'dsb_sc','progression_mode':'screen_guided'}
        app=create_app(directory,text_factory=self.factory,proxy_secret=secret)
        with TestClient(app) as client:
            first=client.post('/lab-sessions',json=body,headers={**alice,'Idempotency-Key':'op-1'})
            self.assertEqual(first.status_code,201); lab_id=first.json()['lab_session_id']
            self.assertNotIn('idempotency-replayed',first.headers)
            again=client.post('/lab-sessions',json=body,headers={**alice,'Idempotency-Key':'op-1'})
            self.assertEqual((again.status_code,again.json()['lab_session_id'],again.headers['idempotency-replayed']),(201,lab_id,'true'))
            self.assertEqual(client.post('/lab-sessions',json={**body,'model_name':'other'},headers={**alice,'Idempotency-Key':'op-1'}).status_code,409)
            bob=client.post('/lab-sessions',json=body,headers={**alice,'x-kiki-owner':'fb:bob-uid','Idempotency-Key':'op-1'})
            self.assertEqual(bob.status_code,201); self.assertNotEqual(bob.json()['lab_session_id'],lab_id)
            unkeyed=[client.post('/lab-sessions',json=body,headers=alice).json()['lab_session_id'] for _ in range(2)]
            self.assertEqual(len({lab_id,*unkeyed}),3)
            self.assertEqual(client.post('/lab-sessions',json=body,headers={**alice,'Idempotency-Key':'bad key!'}).status_code,422)
            self.assertEqual(client.post('/lab-sessions',json=body,headers={**alice,'Idempotency-Key':'op-2','origin':'https://foreign'}).status_code,403)
            self.assertEqual(len(client.get('/lab-sessions',headers=alice).json()),3)
        app.state.store.db.close();app.state.lab.store.db.close();app.state.lab_keys.db.close()
        # The record survives a restart, so a retry after a crash still finds the first lab.
        restarted=create_app(directory,text_factory=self.factory,proxy_secret=secret)
        with TestClient(restarted) as client:
            replay=client.post('/lab-sessions',json=body,headers={**alice,'Idempotency-Key':'op-1'})
            self.assertEqual((replay.status_code,replay.json()['lab_session_id']),(201,lab_id))
        restarted.state.store.db.close();restarted.state.lab.store.db.close();restarted.state.lab_keys.db.close()

    def test_cloud_proxy_boundary_protects_jobs_and_assets(self):
        secret='controlled-proxy-secret-at-least-32-characters'
        app=create_app(self.directory/'cloud',text_factory=self.factory,proxy_secret=secret)
        headers={'x-kiki-proxy-key':secret,'x-kiki-owner':'site-owner',**self.headers}
        with TestClient(app) as client:
            self.assertEqual(client.get('/health').status_code,200)
            self.assertEqual(client.post('/v1/mixed-language-jobs',json=self.body,headers=self.headers).status_code,401)
            job=client.post('/v1/mixed-language-jobs',json=self.body,headers=headers).json()
            self.assertEqual(client.get(job['links']['status'],headers={**headers,'x-kiki-owner':'other'}).status_code,404)
            self.assertEqual(client.get(job['links']['status'],headers=headers).status_code,200)
        app.state.store.db.close();app.state.lab.store.db.close();app.state.lab_keys.db.close()

if __name__=='__main__':unittest.main()
