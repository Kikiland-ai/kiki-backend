"""Authored Python policy for screen-inferred prototype progress, never mastery."""

import copy
import json

from .definition import CHECKPOINTS, expected_condition
from .procedure import PROCEDURES, PROCEDURE_VERSION, COMPLETED, CRITERION_PARTS, OBSERVER_PROMPT, OBSERVER_VERSION

POLICY = {
    'schema': 'screen-guided-policy/v2', 'procedure_version': PROCEDURE_VERSION, 'procedures': PROCEDURES, 'completed_summaries': COMPLETED, 'criterion_parts': CRITERION_PARTS, 'observer_prompt': OBSERVER_PROMPT, 'observer_prompt_version': OBSERVER_VERSION, 'minimum_matches': 2, 'support_age_ms': 120000, 'fast_interval_ms': 3000, 'idle_interval_ms': 12000, 'observer_wire_format': 'lab-observer-json/v3',
    'conditions': {cp_id: expected_condition(cp_id) for cp_id in CHECKPOINTS},
    'confirmations': {'CP-DSB-01': ['CP-DSB-01:workspace', 'CP-DSB-01:project_ref'],
                      'CP-DSB-12': ['CP-DSB-12:saved_model']},
    'responses': {'CP-DSB-10:observation_record': ['observation'],
                  'CP-DSB-11:phase_fault_observation': ['prediction', 'observation'],
                  'CP-DSB-12:explanation': ['explanation']},
    'confirmation_copy': {'CP-DSB-01': "I've created and saved this model", 'CP-DSB-12': "I've saved the restored model"},
    'fallback_confirmations': {'CP-DSB-09': ['CP-DSB-09:baseline_run'], 'CP-DSB-11': ['CP-DSB-11:phase_fault_run'], 'CP-DSB-12': ['CP-DSB-12:restored_run']},
    'fallback_confirmation_copy': 'The simulation finished without errors',
    'response_copy': {'CP-DSB-10': 'What do you notice when you compare the original and recovered signals?',
                      'CP-DSB-11': 'What changed after you shifted the local carrier phase?',
                      'CP-DSB-12': 'Why does carrier alignment matter for recovery?'},
}



def excluded(cp_id):
    return set(POLICY['confirmations'].get(cp_id, [])) | set(POLICY['responses'])


def observe(tracking, criteria, frame_id, now_ms, scope):
    """Repeated visible matches from distinct frames; retain provenance across views."""
    output = copy.deepcopy(tracking)
    for finding in criteria:
        cid = finding['criterion_id']
        old = output.get(cid, {})
        if old.get('scope') != scope or now_ms - old.get('last_seen_ms', 0) > POLICY['support_age_ms']:
            old = {}
        if finding['status'] == 'mismatch':
            output.pop(cid, None)
        elif finding['status'] == 'match' and old.get('last_frame_id') != frame_id:
            output[cid] = {'scope': scope, 'count': min(POLICY['minimum_matches'], old.get('count', 0) + 1),
                           'last_seen_ms': now_ms, 'last_frame_id': frame_id,
                           'frame_ids': (old.get('frame_ids', []) + [frame_id])[-POLICY['minimum_matches']:], 'last_evidence': finding.get('evidence')}
    return {cid: v for cid, v in output.items() if v.get('scope') == scope and now_ms - v['last_seen_ms'] <= POLICY['support_age_ms']}


def supported(tracking, cp_id):
    return {cid for cid, item in tracking.items() if cid not in excluded(cp_id) and item['count'] >= POLICY['minimum_matches']}


def update_procedure_history(history, tracking, findings, scope):
    keys = ('visit_id','workspace_id','parameter_revision','condition')
    output = {aid: v for aid,v in (history or {}).items() if all(v.get('scope',{}).get(k)==scope.get(k) for k in keys)}
    for finding in findings:
        aid=finding['criterion_id']
        if finding['status']=='mismatch':
            output.pop(aid,None)
        elif tracking.get(aid,{}).get('count',0)>=POLICY['minimum_matches']:
            output[aid]=copy.deepcopy(tracking[aid])
    return output


def procedure_plan(cp_id, criteria, tracking=None, now_ms=None, history=None):
    """Historical action progress guides the procedure; it never satisfies a checkpoint."""
    tracking, history = tracking or {}, history or {}
    satisfied = {c['criterion_id'] for c in criteria if c['state'] == 'satisfied'}
    plan=[]
    for item in PROCEDURES.get(cp_id, []):
        support=tracking.get(item['id'],{})
        recent=now_ms is None or now_ms-support.get('last_seen_ms',0)<=POLICY['support_age_ms']
        screen_supported=item['kind']=='visible' and recent and support.get('count',0)>=POLICY['minimum_matches']
        historical=item['kind']=='visible' and history.get(item['id'],{}).get('count',0)>=POLICY['minimum_matches']
        by_criterion=(bool(item['satisfied_by']) and all(cid in satisfied for cid in item['satisfied_by'])) or any(cid in satisfied for cid in item.get('implied_by_any', []))
        plan.append({**item,'tracked':bool(by_criterion or screen_supported or historical),
                     'tracking_basis':'checkpoint_evidence_or_report' if by_criterion else 'recent_screen_support' if screen_supported else 'historical_screen_support' if historical else None})
    return plan


def procedure_guidance(cp_id, criteria, tracking=None, now_ms=None, history=None):
    plan=procedure_plan(cp_id,criteria,tracking,now_ms,history)
    pending=[a for a in plan if not a['tracked']]
    current=pending[0] if pending else None
    if not current:
        missing=[c['criterion_id'] for c in criteria if c['state']!='satisfied']
        checks=[]
        for cid in missing:
            parts=POLICY['criterion_parts'].get(cid,[])
            for item in plan:
                if cid not in item['satisfied_by'] and item['id'] not in parts:
                    continue
                reading=(tracking or {}).get(item['id'],{})
                if parts and reading.get('count',0)>=POLICY['minimum_matches'] and (now_ms is None or now_ms-reading.get('last_seen_ms',0)<=POLICY['support_age_ms']):
                    continue
                how=['Bring the named block’s settings into view and keep the table fields readable. Only change a value if it differs from the table.'] if item['settings'] else ['Bring the named blocks and their existing connections into view, with both endpoints readable.']
                checks.append({**item,'title':item['verify_title'],'how':how if item['kind']=='visible' else item['how'],'verification_only':True})
        pending=checks
        current=pending[0] if pending else None
    return {'procedure':plan,'current_action':current,'next_action':pending[1] if len(pending)>1 else None,
            'action_position':next((i+1 for i,a in enumerate(plan) if current and a['id']==current['id']),len(plan)),
            'procedure_version':PROCEDURE_VERSION,'tracked_in_stage':[{'id':a['id'],'evidence':(tracking or {}).get(a['id'],(history or {}).get(a['id'],{})).get('last_evidence'),'basis':a['tracking_basis']} for a in plan if a['tracked']]}


def guidance(cp_id,criteria,tracking=None,now_ms=None,history=None):
    current=procedure_guidance(cp_id,criteria,tracking,now_ms,history)['current_action']
    return current['title'] if current else 'Keep the completed stage visible while I check its remaining evidence.'


def next_instruction(criteria,upcoming,cp_id=None,tracking=None,now_ms=None,history=None):
    if cp_id:
        value=procedure_guidance(cp_id,criteria,tracking,now_ms,history)
        if value['next_action']:
            return value['next_action']['title']
    return PROCEDURES[upcoming[0]][0]['title'] if upcoming else None


POLICY['stage_explanations'] = {
 'CP-DSB-01':'This saved model will hold the entire transmitter and receiver.',
 'CP-DSB-02':'Message is the signal we want to send. Carrier is the faster signal used to transmit it.',
 'CP-DSB-03':'The message repeats 100 times per second; the carrier repeats 2000 times per second. The table converts these to Simulink’s rad/sec units.',
 'CP-DSB-04':'Multiplying Message by Carrier creates the transmitted DSB-SC signal.',
 'CP-DSB-05':'The receiver needs its own matching reference signal. Local carrier is a third source; Receiver product multiplies that reference by the transmitted signal.',
 'CP-DSB-06':'Lowpass removes the fast components from receiver multiplication. Recovery gain restores the message amplitude.',
 'CP-DSB-07':'The scopes let you compare the source signals, transmitted signal and recovered message without changing the main signal path.',
 'CP-DSB-08':'A short run and small solver steps make the 2000 Hz carrier readable in the simulation.',
 'CP-DSB-09':'This is the first run with matching transmitter and receiver carriers.',
 'CP-DSB-10':'Compare the recovered signal with the original message. A filter can add a small delay and ripple.',
 'CP-DSB-11':'This deliberate phase mismatch tests why the receiver reference must line up with the transmitter carrier.',
 'CP-DSB-12':'Restoring the local reference should bring message recovery back. Save this working model and explain the result.'}
POLICY['actions'] = {cp_id: actions[0]['title'] for cp_id, actions in PROCEDURES.items()}

if __name__ == '__main__':
    print(json.dumps(POLICY, indent=2))
