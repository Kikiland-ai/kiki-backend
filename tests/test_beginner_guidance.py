"""Procedure ordering and the reported Carrier/Local carrier confusion."""
import unittest
from prototypes.lab_tracking.procedure import PROCEDURES, CRITERION_PARTS
from prototypes.lab_tracking.guided import procedure_guidance, observe, POLICY, update_procedure_history
from prototypes.lab_tracking.analysis import build_request, validate_result, AnalysisFailure
from prototypes.lab_tracking.definition import CHECKPOINTS


def criteria(cp):
    return [{'criterion_id':c['id'],'state':'unknown'} for c in CHECKPOINTS[cp]['completion_criteria']]


def tracking(ids):
    return {i:{'count':2,'last_seen_ms':10000,'frame_ids':['f1','f2']} for i in ids}


class BeginnerGuidanceTests(unittest.TestCase):
    def test_all_stages_have_ordered_complete_instruction_cards(self):
        self.assertEqual(set(PROCEDURES),set(CHECKPOINTS))
        all_ids=[]
        for cp,actions in PROCEDURES.items():
            for a in actions:
                self.assertTrue(a['title'] and a['where'] and a['how'] and a['expected_result'] and a['evidence_rule'])
                self.assertEqual(set(a['satisfied_by'])- {c['id'] for c in CHECKPOINTS[cp]['completion_criteria']},set())
                all_ids.append(a['id'])
        self.assertEqual(len(set(all_ids)),len(all_ids))

    def test_receiver_starts_with_creation_not_settings_or_a_missing_filter_reference(self):
        cp='CP-DSB-05'
        guide=procedure_guidance(cp,criteria(cp),{},10000)
        self.assertEqual(guide['current_action']['id'],cp+'/local-create')
        self.assertEqual(guide['next_action']['id'],cp+'/local-settings')
        self.assertIn('third Sine Wave',guide['current_action']['title'])
        self.assertIn('Modulator',guide['current_action']['where'])
        guide=procedure_guidance('CP-DSB-06',criteria('CP-DSB-06'),{},10000)
        self.assertEqual(guide['current_action']['id'],'CP-DSB-06/filter-create')

    def test_local_presence_then_parameters_then_product_then_two_wires(self):
        cp='CP-DSB-05';actions=PROCEDURES[cp]
        for position in range(len(actions)):
            supported=tracking([a['id'] for a in actions[:position]])
            result=procedure_guidance(cp,criteria(cp),supported,10000)
            self.assertEqual(result['current_action']['id'],actions[position]['id'])
            self.assertEqual(result['action_position'],position+1)
        config=actions[1]['settings']
        self.assertIn({'field':'Frequency (rad/sec)','value':'2*pi*2000'},config)
        self.assertIn({'field':'Phase (rad)','value':'pi/2'},config)

    def test_foreign_stale_and_duplicate_action_findings_cannot_move_the_procedure(self):
        cp='CP-DSB-05';aid=PROCEDURES[cp][0]['id'];scope={'visit':'v1'}
        one=observe({},[{'criterion_id':aid,'status':'match','evidence':'Named Local carrier is visible.'}],'f1',10000,scope)
        self.assertEqual(one[aid]['last_evidence'],'Named Local carrier is visible.')
        same=observe(one,[{'criterion_id':aid,'status':'match'}],'f1',11000,scope)
        self.assertEqual(procedure_guidance(cp,criteria(cp),same,11000)['current_action']['id'],aid)
        two=observe(same,[{'criterion_id':aid,'status':'match'}],'f2',12000,scope)
        self.assertNotEqual(procedure_guidance(cp,criteria(cp),two,12000)['current_action']['id'],aid)
        self.assertEqual(procedure_guidance(cp,criteria(cp),two,140000)['current_action']['id'],aid)
        foreign=observe(two,[{'criterion_id':aid,'status':'unknown'}],'f3',13000,{'visit':'v2'})
        self.assertEqual(procedure_guidance(cp,criteria(cp),foreign,13000)['current_action']['id'],aid)

    def test_remembered_actions_do_not_expire_or_complete_checkpoints(self):
        cp='CP-DSB-05';actions=PROCEDURES[cp];scope={'visit_id':'v1','workspace_id':'w1','parameter_revision':0,'condition':'baseline','capture_epoch':1}
        recent={a['id']:{'scope':scope,'count':2,'last_seen_ms':10000,'frame_ids':['f1','f2'],'last_evidence':'Controlled prior observation.'} for a in actions[:2]}
        history=update_procedure_history({},recent,[{'criterion_id':a['id'],'status':'match'} for a in actions[:2]],scope)
        result=procedure_guidance(cp,criteria(cp),{},200000,history)
        self.assertEqual(result['current_action']['id'],cp+'/receiver-create')
        self.assertTrue(all(c['state']=='unknown' for c in criteria(cp)))
        # When all procedure actions were tracked but evidence aged out, ask to show settings, not create duplicates.
        full={a['id']:{'count':2,'last_seen_ms':10000,'frame_ids':['f1','f2']} for a in actions}
        result=procedure_guidance(cp,criteria(cp),{},200000,full)
        self.assertTrue(result['current_action']['verification_only'])
        self.assertEqual(result['current_action']['id'],cp+'/local-settings')
        self.assertIn('Show Local carrier',result['current_action']['title'])
        self.assertEqual(result['next_action']['id'],cp+'/local-wire')
        changed=update_procedure_history(history,{},[],{**scope,'parameter_revision':1})
        self.assertEqual(changed,{})
        contradicted=update_procedure_history(history,{},[{'criterion_id':actions[1]['id'],'status':'mismatch'}],scope)
        self.assertNotIn(actions[1]['id'],contradicted)

    def test_legacy_outputs_remain_conservative_and_new_outputs_validate_ids_and_evidence(self):
        cp=CHECKPOINTS['CP-DSB-05']
        output={'summary':'The Carrier settings dialog is visible.','criteria':[{'criterion_id':c['id'],'status':'unknown','evidence':'Local carrier is not identified in this view.'} for c in cp['completion_criteria']], 'uncertainties':[]}
        self.assertEqual(validate_result(output,cp)['action_findings'],[])
        readings=[{'action_id':a['id'],'status':'unknown','evidence':''} for a in PROCEDURES[cp['id']]]
        value={**output,'action_findings':readings}
        self.assertEqual(len(validate_result(value,cp)['action_findings']),5)
        readings[0]={**readings[0],'action_id':'foreign-action'}
        with self.assertRaises(AnalysisFailure):validate_result(value,cp)
        readings[0]={'action_id':PROCEDURES[cp['id']][0]['id'],'status':'match','evidence':''}
        with self.assertRaises(AnalysisFailure):validate_result(value,cp)

    def test_observer_receives_the_procedure_and_strict_role_rules(self):
        cp=CHECKPOINTS['CP-DSB-05']
        state={'workspace':{'condition':'baseline','model_name':'dsb_demo'},'steps':{cp['id']:{'criteria':criteria(cp['id'])}},'responses':[], 'current_visit_id':'v1'}
        request=build_request(b'jpeg-fixture',cp,state)
        schema=request['generationConfig']['responseJsonSchema']
        self.assertIn('action_findings',schema['required'])
        prompt=request['systemInstruction']['parts'][0]['text']
        self.assertIn('Carrier is the transmitter source',prompt)
        self.assertIn('Unknown is not absent or wrong',prompt)
        self.assertIn("title 'Block Parameters: Carrier'",prompt)
