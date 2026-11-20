"""Preparation acceptance, numerical behaviour, isolation and reusable-pack checks."""
import concurrent.futures
import copy
import json
from pathlib import Path
import tempfile
import unittest

from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError

from contracts.physical_lab import CreatePreparation, ExperimentPack, PreparationEvent
from prototypes.backend.app import create_app
from prototypes.physical_labs.behavior import DsbScBehavior
from prototypes.physical_labs.service import PreparationService, ROOT, load_packs


class PhysicalLabTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.pack = load_packs()['dsb-sc-trainer']
        self.service = PreparationService(self.temp.name)
        self.state = self.service.create('alice', 'first', CreatePreparation(experiment_id='dsb-sc-trainer'))

    def tearDown(self):
        self.temp.cleanup()

    def send(self, kind, **fields):
        event = PreparationEvent(event_id=f'e-{self.state["revision"]}', revision=self.state['revision'], kind=kind, **fields)
        self.state = self.service.event(self.state['session_id'], 'alice', event)
        return self.state

    def enter_concepts(self):
        for target in self.pack['orientation']:
            self.send('select', target=target)
        self.send('advance')

    def answer(self, questions):
        return {q['id']: q['correct'] for q in questions}

    def enter_demonstration(self):
        self.enter_concepts()
        for c in self.pack['concepts']:
            self.send('answer', target=c['id'], answers=self.answer(c['questions']))
        self.send('advance')

    def enter_rehearsal(self):
        self.enter_demonstration()
        for _ in self.pack['steps']:
            self.send('advance')

    def finish_actions(self):
        for step in self.pack['steps']:
            rule = {k: v for k, v in step['rule'].items() if k != 'tolerance'}
            kind = rule.pop('kind')
            self.send(kind, **rule)

    def finish_faults(self):
        for f in self.pack['faults']:
            self.send('answer', target=f['id'], answers=self.answer([f['question']]))
        self.send('advance')

    def test_full_dsb_sc_preparation_receipt_keeps_physical_readings_empty(self):
        self.enter_rehearsal()
        self.assertEqual(self.state['stage'], 'rehearsal')
        self.assertEqual(self.state['apparatus']['connections'], [])
        self.finish_actions()
        self.assertEqual(self.state['stage'], 'faults')
        self.finish_faults()
        self.send('answer', target='readiness', answers=self.answer(self.pack['assessment']))
        receipt = self.service.receipt(self.state['session_id'], 'alice')
        self.assertEqual(receipt['status'], 'prepared')
        self.assertEqual(receipt['physical_execution'], 'not_performed')
        self.assertEqual(receipt['revision_card']['physical_observations']['rows'], [])
        self.assertEqual(receipt['evidence']['english'], 'not_assessed')
        self.assertEqual(receipt['evidence']['words'], 'not_assessed')
        self.assertEqual(receipt['evidence']['independent_steps'], 12)
        self.assertEqual(len(receipt['evidence']['virtual_measurements']), 2)
        self.assertNotIn(['modulator.output', 'scope.input'], self.state['apparatus']['connections'])
        with self.assertRaises(HTTPException):
            self.send('advance')

    def test_stage_skips_and_unearned_receipts_are_rejected(self):
        with self.assertRaises(HTTPException):
            self.service.receipt(self.state['session_id'], 'alice')
        self.enter_concepts()
        with self.assertRaises(HTTPException):
            self.send('advance')
        with self.assertRaises(HTTPException):
            self.send('answer', target='recovery', answers=self.answer(self.pack['concepts'][3]['questions']))

    def test_prerequisites_open_without_an_exhaustive_apparatus_click_gate(self):
        self.send('advance')
        self.assertEqual(self.state['stage'], 'prerequisites')
        questions = self.pack['concepts'][0]['questions']
        self.send('answer', target='signals', answers=self.answer(questions))
        self.assertTrue(self.state['concepts']['signals']['passed'])
        with self.assertRaises(HTTPException):
            self.send('advance')  # Theory readiness is still required for rehearsal.

    def test_prerequisite_threshold_is_sixty_percent_and_retry_is_recorded(self):
        self.enter_concepts()
        questions = self.pack['concepts'][0]['questions']
        answers = self.answer(questions)
        for q in questions[:3]:
            answers[q['id']] = next(k for k in q['options'] if k != q['correct'])
        self.send('answer', target='signals', answers=answers)
        self.assertFalse(self.state['concepts']['signals']['passed'])
        answers[questions[2]['id']] = questions[2]['correct']
        self.send('answer', target='signals', answers=answers)
        self.assertEqual(self.state['concepts']['signals']['percent'], 60)
        self.assertTrue(self.state['concepts']['signals']['passed'])
        self.assertEqual(len(self.state['attempts']), 2)

    def test_wrong_rehearsal_action_and_units_do_not_advance(self):
        self.enter_rehearsal()
        self.send('connect', target='source.carrier', other='modulator.message')
        self.assertEqual(self.state['step_index'], 0)
        self.assertFalse(self.state['feedback']['passed'])
        self.assertEqual(self.state['apparatus']['connections'], [])
        self.send('select', target='modulator.output')
        self.send('set', target='trainer.power', value=True)
        self.send('set', target='source.message_frequency', value=1.0, unit='kHz')
        self.assertEqual(self.state['step_index'], 2)

    def test_readiness_requires_eighty_percent_and_mandatory_handling_question(self):
        self.enter_rehearsal(); self.finish_actions(); self.finish_faults()
        answers = self.answer(self.pack['assessment'])
        last = self.pack['assessment'][-1]
        answers[last['id']] = 'b'
        self.send('answer', target='readiness', answers=answers)
        self.assertEqual(self.state['assessment']['percent'], 80)
        self.assertEqual(self.state['stage'], 'assessment')
        answers[last['id']] = last['correct']
        first = self.pack['assessment'][0]
        answers[first['id']] = 'b'
        self.send('answer', target='readiness', answers=answers)
        self.assertEqual(self.state['stage'], 'prepared')

    def test_create_and_event_retries_are_body_bound_and_owner_scoped(self):
        same = self.service.create('alice', 'first', CreatePreparation(experiment_id='dsb-sc-trainer'))
        self.assertEqual(same['session_id'], self.state['session_id'])
        with self.assertRaises(HTTPException):
            self.service.create('alice', 'first', CreatePreparation(experiment_id='dsb-sc-trainer', language='en'))
        event = PreparationEvent(event_id='retry', revision=0, kind='select', target=self.pack['orientation'][0])
        a = self.service.event(self.state['session_id'], 'alice', event)
        b = self.service.event(self.state['session_id'], 'alice', event)
        self.assertEqual(a, b)
        with self.assertRaises(HTTPException):
            self.service.event(self.state['session_id'], 'alice', event.model_copy(update={'target': 'other'}))
        with self.assertRaises(HTTPException) as error:
            self.service.get(self.state['session_id'], 'bob')
        self.assertEqual(error.exception.status_code, 404)
        with self.assertRaises(HTTPException):
            self.service.event(self.state['session_id'], 'bob', event)

    def test_concurrent_commands_only_commit_one_revision(self):
        def send(i):
            try:
                self.service.event(self.state['session_id'], 'alice', PreparationEvent(
                    event_id=str(i), revision=0, kind='select', target=self.pack['orientation'][i]))
                return 200
            except HTTPException as e:
                return e.status_code
        with concurrent.futures.ThreadPoolExecutor(2) as executor:
            codes = list(executor.map(send, (0, 1)))
        self.assertEqual(sorted(codes), [200, 409])

    def test_restart_uses_pinned_pack_and_resumes_saved_progress(self):
        self.enter_concepts()
        changed = copy.deepcopy(self.pack); changed['version'] = '2.0.0'; changed['title'] = 'Changed'
        restarted = PreparationService(self.temp.name, packs=[changed])
        state = restarted.get(self.state['session_id'], 'alice')
        self.assertEqual(state['stage'], 'prerequisites')
        self.assertEqual(state['pack_version'], self.pack['version'])
        self.assertEqual(restarted.session_pack(state['session_id'], 'alice')['version'], self.pack['version'])

    def test_question_keys_are_never_exposed_before_answers(self):
        pack = self.service.pack('dsb-sc-trainer')
        for c in pack['concepts']:
            for q in c['questions']:
                self.assertNotIn('correct', q)
                self.assertNotIn('explanation', q)
        for q in pack['assessment']:
            self.assertNotIn('correct', q)

    def test_numerical_model_requires_connections_and_predicts_sidebands(self):
        model = DsbScBehavior()
        a = self.service.initial_apparatus(self.pack)
        self.assertFalse(model.observations(self.pack, a)['receiver_connected'])
        a['controls'].update({'trainer.power': True, 'source.message_frequency': 1000.0,
                             'source.carrier_frequency': 82500.0, 'modulator.null': 0.0, 'scope.trigger': 'auto'})
        a['connections'] = self.pack['connections']
        o = model.observations(self.pack, a)
        self.assertEqual(o['spectrum']['sidebands_hz'], [81500, 83500])
        self.assertTrue(o['spectrum']['carrier_suppressed'])
        self.assertEqual(o['readings']['recovered_frequency_hz'], 1000)
        self.assertEqual(o['readings']['recovered_peak_v'], .5)
        for m, recovered in zip(o['traces']['message_v'], o['traces']['recovered_v']):
            self.assertAlmostEqual(recovered, .5 * m)

    def test_pack_rejects_unknown_targets_dependency_cycles_and_unsupported_controls(self):
        cases = []
        p = copy.deepcopy(self.pack); p['orientation'].append('ghost'); cases.append(p)
        p = copy.deepcopy(self.pack); p['concepts'][0]['depends_on'] = ['recovery']; cases.append(p)
        p = copy.deepcopy(self.pack); p['steps'][2]['rule']['value'] = 9999999.0; cases.append(p)
        for p in cases:
            with self.assertRaises(ValidationError):
                ExperimentPack.model_validate(p)
        for value in (float('nan'), float('inf')):
            with self.assertRaises(ValidationError):
                PreparationEvent(event_id='bad', revision=0, kind='set', value=value)

    def test_gltf_contains_real_geometry_and_every_semantic_target(self):
        gltf = json.loads((ROOT / 'assets' / self.pack['asset']).read_text())
        self.assertEqual(gltf['asset']['version'], '2.0')
        self.assertEqual({n['name'] for n in gltf['nodes'] if not n.get('extras', {}).get('decorative')}, {p['id'] for p in self.pack['parts']})
        self.assertGreater(gltf['buffers'][0]['byteLength'], 1000)
        self.assertTrue(gltf['buffers'][0]['uri'].startswith('data:application/octet-stream;base64,'))

    def test_distinct_optical_pack_runs_on_same_pipeline_without_dsb_adapter(self):
        # A test-only second discipline proves the session engine has no DSB target assumptions.
        p = copy.deepcopy(self.pack)
        p.update(id='optical-geometry-fixture', title='Optical geometry fixture', adapter='declarative/v1', demo=None)
        p['parts'] = [dict(id='fiber', label='Fibre', kind='output', position=[0.0,0.0,0.0], size=[.1,.1,.1], description={'en':'Fibre'}),
                      dict(id='screen', label='Screen', kind='control', position=[.2,0.0,0.0], size=[.1,.1,.1], description={'en':'Screen'})]
        p['orientation'] = ['fiber', 'screen']
        c = copy.deepcopy(p['concepts'][0]); c.update(id='geometry', title='Geometry', targets=['fiber','screen'])
        p['concepts'] = [c]; p['controls'] = {'screen': dict(initial=0.0, minimum=0.0, maximum=100.0)}; p['connections'] = []
        p['steps'] = [dict(id='position', instruction={'en':'Position screen'}, why={'en':'Set distance'}, rule=dict(kind='set', target='screen', value=20.0, unit='mm')),
                      dict(id='diameter', instruction={'en':'Read diameter'}, why={'en':'Measure spread'}, rule=dict(kind='measure', target='screen', value=10.0, unit='mm', tolerance=.1)),
                      dict(id='reposition', instruction={'en':'Move screen again'}, why={'en':'Repeat at a new distance'}, rule=dict(kind='set', target='screen', value=40.0, unit='mm')),
                      dict(id='diameter-2', instruction={'en':'Read second diameter'}, why={'en':'Compare spread'}, rule=dict(kind='measure', target='screen', value=20.0, unit='mm', tolerance=.1))]
        p['faults'] = [copy.deepcopy(p['faults'][0])]; p['faults'][0]['target'] = 'screen'
        self.pack = ExperimentPack.model_validate(p).model_dump()
        self.service = PreparationService(Path(self.temp.name)/'optical', packs=[self.pack])
        self.state = self.service.create('alice', 'optical', CreatePreparation(experiment_id=p['id']))
        self.enter_rehearsal(); self.finish_actions(); self.finish_faults()
        self.send('answer', target='readiness', answers=self.answer(self.pack['assessment']))
        self.assertEqual(self.state['stage'], 'prepared')
        self.assertEqual(self.service.observations(self.state['session_id'], 'alice')['model'], 'declarative/v1')

    def test_demo_starts_at_first_connection_and_never_awards_theory_credit(self):
        self.state = self.service.create('alice', 'demo', CreatePreparation(experiment_id=self.pack['id'], mode='experiment_demo'))
        self.assertEqual(self.state['stage'], 'rehearsal')
        self.assertEqual(self.state['activity']['step']['id'], 'message-wire')
        self.assertEqual(self.state['activity']['total'], 9)
        self.assertEqual(self.state['prerequisite_policy'], 'assumed_for_demo')
        self.assertEqual(self.state['apparatus']['connections'], [])
        self.assertTrue(self.state['apparatus']['controls']['trainer.power'])
        self.send('connect', target='source.carrier', other='modulator.message')
        self.assertEqual(self.state['procedure_index'], 0)
        self.assertFalse(self.state['feedback']['passed'])
        for step in self.pack['steps']:
            if step['id'] in self.pack['demo']['omit_step_ids']:
                continue
            rule = {k:v for k,v in step['rule'].items() if k != 'tolerance'}
            self.send(rule.pop('kind'), **rule)
        self.assertEqual(self.state['stage'], 'experiment_complete')
        self.assertEqual(self.state['concepts'], {})
        result = self.service.experiment_result(self.state['session_id'], 'alice')
        self.assertFalse(result['theory_assessed'])
        self.assertEqual(result['physical_execution'], 'not_performed')
        self.assertEqual(result['readings']['recovered_frequency_hz'], 1000)
        self.assertEqual(result['readings']['recovered_peak_v'], .5)
        self.assertTrue(all(a['context']=='virtual_experiment_demo' for a in self.state['attempts']))
        with self.assertRaises(HTTPException):
            self.service.receipt(self.state['session_id'], 'alice')
        restarted = PreparationService(self.temp.name)
        self.assertEqual(restarted.get(self.state['session_id'],'alice')['stage'], 'experiment_complete')

    def test_demo_does_not_change_normal_gates_and_cannot_preset_connections(self):
        self.assertEqual(self.state['mode'], 'guided_preparation')
        self.assertEqual(self.state['stage'], 'orientation')
        self.send('advance')
        with self.assertRaises(HTTPException):
            self.send('advance')
        with self.assertRaises(HTTPException):
            self.service.experiment_result(self.state['session_id'],'alice')
        invalid=copy.deepcopy(self.pack)
        invalid['demo']['omit_step_ids'].append('message-wire')
        with self.assertRaises(ValidationError):
            ExperimentPack.model_validate(invalid)

    def test_mode_is_bound_to_creation_idempotency(self):
        with self.assertRaises(HTTPException) as error:
            self.service.create('alice','first',CreatePreparation(experiment_id=self.pack['id'], mode='experiment_demo'))
        self.assertEqual(error.exception.status_code,409)


class PhysicalLabApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.app = create_app(Path(self.temp.name), proxy_secret='')
        self.client = TestClient(self.app)
        self.client.get('/')
        self.headers = {'Origin': 'http://testserver', 'Idempotency-Key': 'physical-1'}

    def tearDown(self):
        self.client.close()
        for store in (self.app.state.store, self.app.state.lab.store, self.app.state.lab_keys, self.app.state.mixed_language):
            store.db.close()
        self.app.state.mixed_language.executor.shutdown(wait=False)
        self.temp.cleanup()

    def test_catalogue_assets_and_openapi_are_served(self):
        base = '/v1/physical-labs'
        catalogue = self.client.get(base+'/experiments')
        self.assertEqual(catalogue.status_code, 200)
        self.assertEqual(catalogue.json()[0]['id'], 'dsb-sc-trainer')
        self.assertEqual(self.client.get(base+'/assets/dsb-sc-trainer-v1.gltf').status_code, 200)
        self.assertEqual(self.client.get(base+'/assets/dsb-sc-trainer-v2.gltf').status_code, 200)
        self.assertEqual(self.client.get(base+'/assets/unknown.gltf').status_code, 404)
        self.assertEqual(self.client.get(base+'/preview').status_code, 404)
        paths = self.client.get('/openapi.json').json()['paths']
        self.assertIn(base+'/sessions/{session_id}/events', paths)
        self.assertIn('requestBody', paths[base+'/sessions']['post'])

    def test_prerequisite_button_can_open_and_submit_first_lesson_immediately(self):
        base = '/v1/physical-labs'
        state = self.client.post(base+'/sessions', json={'experiment_id':'dsb-sc-trainer'}, headers=self.headers).json()
        event = {'event_id':'open-lessons', 'revision':0, 'kind':'advance'}
        opened = self.client.post(state['links']['events'], json=event, headers=self.headers)
        self.assertEqual(opened.status_code, 200)
        self.assertEqual(opened.json()['stage'], 'prerequisites')
        concept = load_packs()['dsb-sc-trainer']['concepts'][0]
        event = {'event_id':'first-check','revision':1,'kind':'answer','target':concept['id'],
                 'answers':{q['id']:q['correct'] for q in concept['questions']}}
        checked = self.client.post(state['links']['events'], json=event, headers=self.headers)
        self.assertEqual(checked.status_code,200)
        self.assertTrue(checked.json()['concepts'][concept['id']]['passed'])

    def test_owner_origin_limits_and_forged_progress(self):
        base = '/v1/physical-labs'
        body = {'experiment_id': 'dsb-sc-trainer'}
        response = self.client.post(base+'/sessions', json=body, headers=self.headers)
        self.assertEqual(response.status_code, 201, response.text)
        url = response.json()['links']['self']
        with TestClient(self.app) as stranger:
            self.assertEqual(stranger.get(base+'/experiments').status_code, 401)
            stranger.get('/')
            self.assertEqual(stranger.get(url).status_code, 404)
        self.assertEqual(self.client.post(base+'/sessions', json=body, headers={**self.headers, 'Origin':'https://foreign'}).status_code, 403)
        self.assertEqual(self.client.post(base+'/sessions', json={**body, 'passed':True}, headers=self.headers).status_code, 422)
        self.assertEqual(self.client.post(url+'/events', json={'event_id':'fake','revision':0,'kind':'complete'}, headers=self.headers).status_code, 422)
        self.assertEqual(self.client.post(base+'/sessions', content=b'x'*16001, headers=self.headers).status_code, 413)


if __name__ == '__main__':
    unittest.main()
