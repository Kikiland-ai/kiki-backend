"""Python pipeline/API acceptance with real JPEGs and explicit synthetic model findings."""

import asyncio
import base64
import copy
import hashlib
import io
import json
import tempfile
import time
import unittest
from pathlib import Path

import httpx
from fastapi import HTTPException
from fastapi.testclient import TestClient
from PIL import Image

from contracts.lab_tracking import AttachCapture, CheckFrame, ContextChange, ReviewCriteria, StartLab, StudentResponse
from prototypes.lab_tracking.analysis import AnalysisFailure, GeminiAnalyzer, validate_result
from prototypes.lab_tracking.definition import CHECKPOINTS, ORDER
from prototypes.lab_tracking.service import LabService
from prototypes.lab_tracking.guided import observe, supported
from prototypes.screen_capture.server import create_app


def jpeg():
    buffer = io.BytesIO()
    Image.new('RGB', (96, 54), (20, 90, 150)).save(buffer, format='JPEG')
    return buffer.getvalue()


def findings(cp):
    return {'summary': 'Synthetic model finding; not actual Simulink recognition.',
            'criteria': [{'criterion_id': c['id'], 'status': 'unknown', 'evidence': 'Controlled JPEG fixture.'} for c in cp['completion_criteria']], 'uncertainties': []}


class Clock:
    def __init__(self):
        self.value = time.time()

    def __call__(self):
        return self.value

    def tick(self, seconds):
        self.value += seconds


class FakeAnalyzer:
    configured = True
    model = 'controlled_fixture_no_provider'
    prompt_version = 'controlled_fixture/v1'

    def __init__(self):
        self.calls = []

    async def analyze(self, pixels, cp, state):
        self.calls.append((pixels, copy.deepcopy(cp), copy.deepcopy(state)))
        return findings(cp)


class LabTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.clock = Clock()
        self.analyzer = FakeAnalyzer()
        self.pixels = jpeg()
        self.capture = {'status': 'sharing', 'frame': None, 'pixels': self.pixels}
        self.service = LabService(Path(self.temp.name), lambda sid, owner: self.capture, analyzer=self.analyzer, clock=self.clock)
        self.state = self.service.start('owner', StartLab(model_name='dsb_sc_fixture', operator_trial=True))
        self.lab_id = self.state['lab_session_id']
        self.state = self.service.attach(self.lab_id, 'owner', AttachCapture(revision=self.state['revision'], capture_session_id='capture'))
        self.sequence = 0
        self.frame()

    def tearDown(self):
        self.service.store.db.close()
        self.temp.cleanup()

    def frame(self):
        self.sequence += 1
        self.capture['frame'] = {'frame_id': f'capture:1:{self.sequence}', 'sha256': hashlib.sha256(self.pixels).hexdigest(),
            'server_received_unix': self.clock(), 'server_received_at': self.service.timestamp(), 'sequence': self.sequence,
            'captured_elapsed_ms': self.sequence * 2000, 'view_revision': self.state['workspace']['view_revision'],
            'width': 96, 'height': 54, 'byte_count': len(self.pixels), 'mime_type': 'image/jpeg'}

    def change(self, **fields):
        self.state = self.service.change(self.lab_id, 'owner', ContextChange(revision=self.state['revision'], **fields))

    async def check(self):
        self.state = await self.service.check(self.lab_id, 'owner', CheckFrame(revision=self.state['revision'], frame_id=self.capture['frame']['frame_id'], view_revision=self.state['workspace']['view_revision']))

    def response(self, kind='observation'):
        self.state = self.service.respond(self.lab_id, 'owner', StudentResponse(revision=self.state['revision'], kind=kind,
            text='Synthetic student report for policy verification only.', self_confidence=2))

    def review(self, criterion_ids=None):
        ids = criterion_ids or [c['criterion_id'] for c in self.state['steps'][self.state['queue']['current_checkpoint_id']]['criteria']]
        self.state = self.service.review(self.lab_id, 'owner', ReviewCriteria(revision=self.state['revision'], criterion_ids=ids,
            review_note='Synthetic operator acceptance to exercise the checkpoint policy.'))

    async def test_complete_twelve_checkpoint_run_with_fault_restore_and_typed_responses(self):
        for cp_id in ORDER:
            self.assertEqual(self.state['queue']['current_checkpoint_id'], cp_id)
            if cp_id in ('CP-DSB-11', 'CP-DSB-12'):
                self.frame()
                await self.check()
                with self.assertRaises(HTTPException) as caught:
                    self.review()
                self.assertEqual(caught.exception.status_code, 409, 'Wrong condition cannot complete fault/restoration steps')
                self.clock.tick(10)
                self.change(action='condition', condition='phase_fault' if cp_id == 'CP-DSB-11' else 'restored_baseline')
            self.frame()
            await self.check()
            self.assertNotIn(cp_id, self.state['queue']['done_checkpoint_ids'], 'Analysis must not complete a checkpoint')
            if cp_id in ('CP-DSB-10', 'CP-DSB-11', 'CP-DSB-12'):
                with self.assertRaises(HTTPException) as caught:
                    self.review()
                self.assertEqual(caught.exception.status_code, 422, 'Output/run evidence cannot replace the required student report')
                self.response('explanation' if cp_id == 'CP-DSB-12' else 'observation')
            self.review()
            self.assertEqual(self.state['steps'][cp_id]['status'], 'done')
            self.clock.tick(11)
        self.assertEqual(self.state['status'], 'completed')
        self.assertEqual(self.state['queue']['done_checkpoint_ids'], ORDER)
        self.assertIsNone(self.state['runtime']['candidate'])
        self.assertFalse(self.service.images)
        self.assertTrue(all(c['understanding'] == 'unknown' for c in self.state['learner_state']['concepts']))
        events = self.service.store.events(self.lab_id, 'owner')
        self.assertEqual([e['context']['checkpoint_id'] for e in events if e['event_type'] == 'checkpoint_completed'], ORDER)
        self.assertTrue(all('view_revision' in e['context'] for e in events))
        self.assertEqual(len(self.analyzer.calls), 14)

    async def test_fast_check_interval_keeps_admission_and_review_boundaries(self):
        await self.check()
        self.clock.tick(2);self.frame()
        with self.assertRaises(HTTPException) as caught: await self.check()
        self.assertEqual(caught.exception.status_code,429)
        self.assertEqual(len(self.analyzer.calls),1)
        self.clock.tick(1);self.frame();await self.check()
        self.assertEqual(len(self.analyzer.calls),2)
        self.assertEqual(self.state['queue']['done_checkpoint_ids'],[])
        self.assertIn('total_ms',self.state['runtime']['last_analysis_timing'])

    async def test_reviewed_mode_still_requires_review_and_reads_continue_past_thirty(self):
        async def matches(pixels, cp, state):
            value = findings(cp)
            for c in value['criteria']:
                c['status'] = 'match'
            return value
        self.analyzer.analyze = matches
        await self.check()
        self.assertEqual(self.state['queue']['done_checkpoint_ids'], [])
        self.assertTrue(all(c['state'] == 'unknown' for c in self.state['steps'][ORDER[0]]['criteria']))
        with self.assertRaises(HTTPException) as caught:
            await self.check()
        self.assertEqual(caught.exception.status_code, 429)
        saved = self.service.load(self.lab_id, 'owner')
        saved['runtime']['analysis_attempts'] = 30
        self.service.save(saved, 'fixture_past_previous_cap')
        self.state = self.service.project(self.service.load(self.lab_id, 'owner'))
        self.clock.tick(11); self.frame()
        await self.check()
        self.assertEqual(self.state['runtime']['analysis_attempts'], 31)
        self.assertEqual(self.state['queue']['done_checkpoint_ids'], [])

    async def test_responses_and_journal_continue_beyond_former_caps(self):
        for i in range(510):
            self.state = self.service.respond(self.lab_id, 'owner', StudentResponse(revision=self.state['revision'], kind='note', text=f'Controlled response {i}'))
        self.assertGreater(self.state['revision'], 500)
        self.assertEqual(len(self.state['responses']), 100)
        events, after = [], 0
        while True:
            page = self.service.store.events(self.lab_id, 'owner', after, 100)
            events.extend(page)
            if len(page) < 100:
                break
            after = page[-1]['event_sequence']
        responses = [e['payload'] for e in events if e['event_type'] == 'student_response']
        self.assertEqual(len(responses), 510)
        self.assertEqual(responses[0]['text'], 'Controlled response 0')
        self.assertEqual(responses[-1]['text'], 'Controlled response 509')

    async def test_context_change_clears_partial_criteria_but_keeps_historical_evidence(self):
        await self.check()
        self.review([self.state['steps'][ORDER[0]]['criteria'][0]['criterion_id']])
        evidence = copy.deepcopy(self.state['evidence'])
        self.change(action='parameters_changed')
        self.assertTrue(all(c['state'] == 'unknown' for c in self.state['steps'][ORDER[0]]['criteria']))
        self.assertEqual(self.state['evidence'], evidence)

    async def test_partial_reviews_and_duplicate_revision_cannot_advance_twice(self):
        await self.check()
        ids = [c['criterion_id'] for c in self.state['steps'][ORDER[0]]['criteria']]
        self.review([ids[0]])
        self.assertEqual(self.state['queue']['current_checkpoint_id'], ORDER[0])
        old = self.state['revision']
        self.review([ids[1]])
        with self.assertRaises(HTTPException) as caught:
            self.service.review(self.lab_id, 'owner', ReviewCriteria(revision=old, criterion_ids=[ids[1]], review_note='Duplicate operator submission.'))
        self.assertEqual(caught.exception.status_code, 409)
        self.assertEqual(self.state['queue']['done_checkpoint_ids'], [ORDER[0]])

    async def test_guided_visible_step_advances_automatically_but_stays_unassessed(self):
        await self.check(); self.review()  # explicit workspace/save confirmation
        self.change(action='enable_guided')
        async def matches(pixels, cp, state):
            value = findings(cp)
            for c in value['criteria']: c['status'] = 'match'
            return value
        self.analyzer.analyze = matches
        self.clock.tick(11); self.frame(); await self.check()
        self.assertEqual(self.state['queue']['current_checkpoint_id'], ORDER[1])
        self.clock.tick(11); self.frame(); await self.check()
        self.assertEqual(self.state['queue']['current_checkpoint_id'], ORDER[2])
        done = self.state['steps'][ORDER[1]]
        self.assertEqual(done['assessment_status'], 'unassessed')
        self.assertEqual(done['completion_basis'], 'screen_inferred_or_student_report')
        self.assertTrue(all(c['completion_basis']=='screen_inferred' for c in done['criteria']))
        self.assertTrue(any(e.get('review_status')=='unreviewed' for e in self.state['evidence']))
        self.assertTrue(all(c['understanding']=='unknown' for c in self.state['learner_state']['concepts']))
        self.assertIsNone(self.state['runtime']['candidate'])
        self.assertNotIn(self.lab_id, self.service.images)

    async def test_guided_save_confirmation_cannot_be_invented_by_a_model(self):
        self.change(action='enable_guided')
        async def matches(pixels, cp, state):
            value=findings(cp)
            for c in value['criteria']: c['status']='match'
            return value
        self.analyzer.analyze=matches
        for _ in range(2):
            self.frame(); await self.check(); self.clock.tick(11)
        self.assertEqual(self.state['queue']['current_checkpoint_id'], ORDER[0])
        self.assertTrue(all(c['state']=='unknown' for c in self.state['steps'][ORDER[0]]['criteria']))

    async def test_phase_fields_are_tracked_across_dialogs_and_mismatch_invalidates_the_combination(self):
        cp_id='CP-DSB-11'
        state=self.service.load(self.lab_id,'owner')
        state.update(progression_mode='screen_guided')
        state['queue']={'current_checkpoint_id':cp_id,'done_checkpoint_ids':ORDER[:10],'upcoming_checkpoint_ids':ORDER[11:]}
        state['workspace']['condition']='phase_fault'
        state['steps'][cp_id]['status']='in_progress'
        state['steps'][cp_id]['current_visit_id']='phase-visit'
        state['current_visit_id']='phase-visit'
        self.state=self.service.save(state,'controlled_phase_fixture')
        from prototypes.lab_tracking.procedure import PROCEDURES
        scene=['local']
        async def phase_findings(pixels,cp,state):
            result=findings(cp)
            result['action_findings']=[{'action_id':a['id'], 'status':'match' if (scene[0]=='local' and a['id'].endswith('/phase')) or (scene[0]=='carrier' and a['id'].endswith('/carrier-check')) else 'mismatch' if scene[0]=='wrong-carrier' and a['id'].endswith('/carrier-check') else 'unknown', 'evidence':'Controlled named phase field fixture.'} for a in PROCEDURES[cp_id]]
            return result
        self.analyzer.analyze=phase_findings
        for _ in range(2):
            self.clock.tick(11);self.frame();await self.check()
        self.assertEqual(self.state['guidance']['current_action']['id'],cp_id+'/carrier-check')
        self.assertEqual(self.state['steps'][cp_id]['criteria'][0]['state'],'unknown')
        scene[0]='carrier'
        for _ in range(2):
            self.clock.tick(11);self.frame();await self.check()
        self.assertEqual(self.state['steps'][cp_id]['criteria'][0]['state'],'satisfied')
        self.assertEqual(self.state['guidance']['current_action']['id'],cp_id+'/run')
        self.assertEqual(self.state['queue']['current_checkpoint_id'],cp_id)
        scene[0]='wrong-carrier';self.clock.tick(11);self.frame();await self.check()
        self.assertEqual(self.state['steps'][cp_id]['criteria'][0]['state'],'unknown')
        self.assertEqual(self.state['guidance']['current_action']['id'],cp_id+'/carrier-check')

    async def test_guided_policy_repeated_frame_mismatch_and_context_expiry(self):
        cp=ORDER[1]; ids=[c['id'] for c in CHECKPOINTS[cp]['completion_criteria']]
        entries=[{'criterion_id':cid,'status':'match','evidence':'fixture'} for cid in ids]
        scope={'visit_id':'fixture','parameter_revision':1}
        tracked=observe({},entries,'frame-1',0,scope)
        tracked=observe(tracked,entries,'frame-1',1000,scope)
        self.assertEqual(supported(tracked,cp),set(),'Same frame cannot supply two observations')
        tracked=observe(tracked,entries,'frame-2',12000,scope)
        self.assertEqual(supported(tracked,cp),set(ids))
        tracked=observe(tracked,[dict(entries[0],status='mismatch')],'frame-3',13000,scope)
        self.assertNotIn(ids[0],supported(tracked,cp))
        self.assertFalse(supported(observe(tracked,[], 'frame-4',140000,scope),cp))
        self.assertFalse(supported(observe(tracked,entries,'frame-5',150000,{'visit_id':'new','parameter_revision':2}),cp))

    async def test_failure_keeps_previous_candidate_counts_attempt_and_recovers(self):
        await self.check()
        previous = self.state['runtime']['candidate']['observation_id']
        async def fail(*args):
            raise AnalysisFailure('provider_http_503')
        self.analyzer.analyze = fail
        self.clock.tick(10)
        self.frame()
        await self.check()
        self.assertEqual(self.state['runtime']['analysis_status'], 'waiting_for_provider')
        self.assertEqual(self.state['runtime']['candidate']['observation_id'], previous)
        self.assertEqual(self.state['runtime']['analysis_attempts'], 2)
        self.analyzer.analyze = FakeAnalyzer().analyze
        self.clock.tick(10)
        self.frame()
        await self.check()
        self.assertNotEqual(self.state['runtime']['candidate']['observation_id'], previous)

    async def test_late_result_after_view_visit_or_parameter_change_is_discarded(self):
        for change in ({'action': 'view_changed', 'view_revision': 2}, {'action': 'revisit', 'checkpoint_id': ORDER[0]}, {'action': 'parameters_changed'}):
            entered, release = asyncio.Event(), asyncio.Event()
            async def blocked(pixels, cp, state):
                entered.set()
                await release.wait()
                return findings(cp)
            self.analyzer.analyze = blocked
            self.frame()
            task = asyncio.create_task(self.check())
            await entered.wait()
            self.state = self.service.project(self.service.load(self.lab_id, 'owner'))
            self.change(**change)
            release.set()
            with self.assertRaises(HTTPException) as caught:
                await task
            self.assertEqual(caught.exception.status_code, 409)
            self.assertIsNone(self.service.load(self.lab_id, 'owner')['runtime']['candidate'])
            self.clock.tick(11)

    async def test_new_capture_frames_do_not_change_analysed_pixel_provenance(self):
        entered, release = asyncio.Event(), asyncio.Event()
        async def blocked(pixels, cp, state):
            entered.set()
            await release.wait()
            return findings(cp)
        self.analyzer.analyze = blocked
        original = copy.deepcopy(self.capture['frame'])
        task = asyncio.create_task(self.check())
        await entered.wait()
        self.frame()
        release.set()
        await task
        self.assertEqual(self.state['runtime']['candidate']['source_frame'], original)
        image, candidate = self.service.image(self.lab_id, 'owner', self.state['runtime']['candidate']['frame_handle']['handle_id'])
        self.assertEqual(image, self.pixels)
        self.assertEqual(candidate['source_frame']['sha256'], hashlib.sha256(image).hexdigest())

    async def test_pause_disconnect_and_restart_preserve_queue_but_invalidate_pixels(self):
        await self.check()
        self.change(action='pause')
        self.assertFalse(self.service.images)
        self.assertEqual(self.state['queue']['current_checkpoint_id'], ORDER[0])
        self.change(action='resume')
        self.service.capture_changed('capture', 'disconnected')
        self.state = self.service.project(self.service.load(self.lab_id, 'owner'))
        self.assertEqual(self.state['guidance']['state'], 'disconnected')
        self.clock.tick(5)
        restarted = LabService(Path(self.temp.name), lambda sid, owner: self.capture, analyzer=self.analyzer, clock=self.clock)
        try:
            loaded = restarted.load(self.lab_id, 'owner')
            self.assertEqual(loaded['queue']['current_checkpoint_id'], ORDER[0])
            self.assertEqual(loaded['runtime']['analysis_attempts'], 1)
            self.assertIsNone(loaded['runtime']['candidate'])
            self.assertGreaterEqual(loaded['steps'][ORDER[0]]['timing']['disconnected_ms'], 5000)
        finally:
            restarted.store.db.close()

    async def test_timing_splits_pause_and_disconnect_without_assessing_understanding(self):
        self.clock.tick(5)
        self.change(action='pause')
        self.clock.tick(3)
        self.change(action='resume')
        self.clock.tick(2)
        self.service.capture_changed('capture', 'disconnected')
        self.clock.tick(4)
        self.state = self.service.project(self.service.load(self.lab_id, 'owner'))
        timing = self.state['steps'][ORDER[0]]['timing']
        self.assertEqual(timing['wall_ms'], 14000)
        self.assertEqual(timing['tracking_active_ms'], 7000)
        self.assertEqual(timing['paused_ms'], 3000)
        self.assertEqual(timing['disconnected_ms'], 4000)

    async def test_foreign_or_expired_frame_never_calls_provider(self):
        with self.assertRaises(HTTPException):
            await self.service.check(self.lab_id, 'owner', CheckFrame(revision=self.state['revision'], frame_id='foreign', view_revision=1))
        self.clock.tick(7)
        with self.assertRaises(HTTPException):
            await self.check()
        self.assertEqual(self.analyzer.calls, [])

    async def test_handle_expiry_and_review_expiry_are_independent(self):
        await self.check()
        handle = self.state['runtime']['candidate']['frame_handle']['handle_id']
        self.clock.tick(9)
        with self.assertRaises(HTTPException):
            self.service.image(self.lab_id, 'owner', handle)
        self.assertEqual(self.service.image(self.lab_id, 'owner')[0], self.pixels)
        self.clock.tick(12)
        with self.assertRaises(HTTPException):
            self.review()

    async def test_foreign_owner_and_duplicate_criterion_are_rejected(self):
        with self.assertRaises(HTTPException) as caught:
            self.service.load(self.lab_id, 'foreign')
        self.assertEqual(caught.exception.status_code, 404)
        await self.check()
        cid = self.state['steps'][ORDER[0]]['criteria'][0]['criterion_id']
        with self.assertRaises(HTTPException):
            self.review([cid, cid])


class ProviderTests(unittest.IsolatedAsyncioTestCase):
    async def test_exact_jpeg_and_strict_model_output_with_real_http_adapter(self):
        pixels, cp = jpeg(), CHECKPOINTS[ORDER[0]]
        captured = []
        def handler(request):
            body = json.loads(request.content)
            captured.append(body)
            return httpx.Response(200, json={'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': json.dumps(findings(cp))}]}}]})
        state = {'workspace': {'condition': 'baseline'}, 'steps': {cp['id']: {'criteria': []}}, 'responses': [], 'current_visit_id': 'fixture'}
        result = await GeminiAnalyzer('fixture-only', httpx.MockTransport(handler)).analyze(pixels, cp, state)
        self.assertEqual(base64.b64decode(captured[0]['contents'][0]['parts'][1]['inlineData']['data']), pixels)
        self.assertEqual(result['criteria'][0]['status'], 'unknown')

    async def test_model_override_uses_low_thinking_and_actual_model(self):
        pixels, cp = jpeg(), CHECKPOINTS[ORDER[0]]
        captured=[]
        def handler(request):
            captured.append((str(request.url), json.loads(request.content)))
            return httpx.Response(200,json={'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':json.dumps(findings(cp))}]}}]})
        state={'workspace':{'condition':'baseline'},'steps':{cp['id']:{'criteria':[]}},'responses':[],'current_visit_id':'fixture'}
        analyzer=GeminiAnalyzer('fixture-only',httpx.MockTransport(handler),model='gemini-3.8-flash')
        await analyzer.analyze(pixels,cp,state)
        self.assertEqual(analyzer.model,'gemini-3.8-flash')
        self.assertIn('/gemini-3.8-flash:generateContent',captured[0][0])
        self.assertEqual(captured[0][1]['generationConfig']['thinkingConfig']['thinkingLevel'],'low')
        self.assertNotIn('temperature',captured[0][1]['generationConfig'])

    async def test_duplicate_unknown_and_oversized_model_fields_are_rejected(self):
        cp = CHECKPOINTS[ORDER[0]]
        for mutate in (lambda v: v['criteria'].append(v['criteria'][0]), lambda v: v.update(extra='untrusted'), lambda v: v['criteria'][0].update(criterion_id='foreign'), lambda v: v.update(summary='x'*221), lambda v: v.update(uncertainties=['x'*151])):
            value = findings(cp)
            mutate(value)
            with self.assertRaises(AnalysisFailure):
                validate_result(value, cp)


class APITests(unittest.TestCase):
    def test_websocket_capture_to_python_analysis_review_and_export(self):
        with tempfile.TemporaryDirectory() as directory:
            analyzer = FakeAnalyzer()
            app = create_app(Path(directory), analyzer=analyzer)
            client = TestClient(app)
            try:
                client.get('/')
                headers = {'origin': 'http://testserver'}
                lab = client.post('/lab-sessions', headers=headers, json={'model_name': 'dsb_sc_fixture', 'operator_trial': True}).json()
                lab_id = lab['lab_session_id']
                self.assertNotIn('owner_id', lab, 'Never export the HTTP-only bearer capability')
                capture_id = client.post('/screen-sessions', headers=headers).json()['session_id']
                pixels = jpeg()
                with client.websocket_connect(f'/screen-sessions/{capture_id}/stream', headers=headers) as ws:
                    ws.receive_json(); ws.send_json({'type': 'capture_started'}); ws.receive_json()
                    meta = {'type': 'frame', 'capture_epoch': 1, 'view_revision': 1, 'sequence': 1, 'captured_elapsed_ms': 20, 'width': 96, 'height': 54, 'source_width': 96, 'source_height': 54, 'byte_count': len(pixels), 'mime_type': 'image/jpeg'}
                    ws.send_json(meta); ws.send_bytes(pixels)
                    frame = ws.receive_json()['observation']['observation']['latest_frame']
                    lab = client.post(f'/lab-sessions/{lab_id}/attach', headers=headers, json={'revision': lab['revision'], 'capture_session_id': capture_id}).json()
                    response = client.post(f'/lab-sessions/{lab_id}/check', headers=headers, json={'revision': lab['revision'], 'frame_id': frame['frame_id'], 'view_revision': 1})
                    self.assertEqual(response.status_code, 200, response.text)
                    lab = response.json()
                    handle = lab['runtime']['candidate']['frame_handle']['handle_id']
                    self.assertEqual(client.get(f'/lab-sessions/{lab_id}/frame-handles/{handle}').content, pixels)
                    rpc = {'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': 'read_checked_frame', 'arguments': {'lab_session_id': lab_id}}}
                    checked = client.post('/mcp', json=rpc).json()['result']['content']
                    self.assertEqual(base64.b64decode(checked[1]['data']), pixels)
                    self.assertEqual(json.loads(checked[0]['text'])['source_frame']['sha256'], hashlib.sha256(pixels).hexdigest())
                    response = client.post(f'/lab-sessions/{lab_id}/review', headers=headers, json={'revision': lab['revision'], 'criterion_ids': [c['criterion_id'] for c in lab['steps'][ORDER[0]]['criteria']], 'review_note': 'Controlled operator review of the test image.'})
                    self.assertEqual(response.status_code, 200, response.text)
                    self.assertEqual(response.json()['queue']['current_checkpoint_id'], ORDER[1])
                    self.assertEqual(client.get(f'/lab-sessions/{lab_id}/frame-handles/{handle}').status_code, 410)
                    self.assertTrue(client.post('/mcp', json=rpc).json()['result']['isError'])
                exported = client.get(f'/lab-sessions/{lab_id}/export').json()
                self.assertEqual(exported['state']['queue']['done_checkpoint_ids'], [ORDER[0]])
                self.assertTrue(all(p.name.startswith(('sessions.sqlite', 'labs.sqlite')) for p in Path(directory).iterdir()))
                before=exported['state']
                reset_rpc={'jsonrpc':'2.0','id':19,'method':'tools/call','params':{'name':'reset_lab_session','arguments':{'lab_session_id':lab_id,'revision':before['revision']}}}
                reset=client.post('/mcp',json=reset_rpc)
                self.assertEqual(reset.status_code,200)
                restarted=json.loads(reset.json()['result']['content'][0]['text'])
                self.assertEqual(restarted['queue']['current_checkpoint_id'],ORDER[0])
                self.assertEqual(restarted['queue']['done_checkpoint_ids'],[])
                self.assertEqual(restarted['evidence'],before['evidence'])
                self.assertNotEqual(restarted['current_visit_id'],before['steps'][ORDER[0]]['current_visit_id'])
                self.assertEqual(client.post('/mcp',json=reset_rpc).status_code,409)
                self.assertEqual(client.post(f'/lab-sessions/{lab_id}/context', headers={'origin': 'https://foreign'}, json={'revision': 1, 'action': 'pause'}).status_code, 403)
                outsider = TestClient(app); outsider.get('/')
                self.assertEqual(outsider.get(f'/lab-sessions/{lab_id}').status_code, 404)
                outsider.close()
            finally:
                client.close(); app.state.store.db.close(); app.state.lab.store.db.close()


if __name__ == '__main__':
    unittest.main()
