"""Validate the proposed DSB-SC definition/example and key cross-field invariants.

Uses jsonschema already available in this executor; does not run Simulink or a provider.
This is a design check, not a live session reducer or API implementation.
"""
import copy
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker, ValidationError

ROOT=Path(__file__).resolve().parents[1]
DEFINITION=ROOT/'docs/architecture/examples/dsb-sc.demo-definition.json'
EXAMPLE=ROOT/'docs/architecture/examples/lab-tracking.synthetic.example.json'
SCHEMA=ROOT/'contracts/lab_tracking.schema.json'
definition=json.loads(DEFINITION.read_text())
example=json.loads(EXAMPLE.read_text())
validator=Draft202012Validator(json.loads(SCHEMA.read_text()),format_checker=FormatChecker())
Draft202012Validator.check_schema(validator.schema)


def check(value):
    validator.validate(value)
    assert value['definition']['definition_sha256']==hashlib.sha256(DEFINITION.read_bytes()).hexdigest(), 'Definition changed without rebind'
    definitions={c['id']:c for c in definition['checkpoints']}
    states={s['checkpoint_id']:s for s in value['steps']}
    assert len(states)==12 and set(states)==set(definitions), 'Duplicate or missing checkpoint states'
    concepts={c['concept_id'] for c in value['learner_state']['concepts']}
    assert len(value['learner_state']['concepts'])==len(concepts)==7, 'Duplicate concept state'
    assert concepts==set(definition['readiness']['required_concept_ids']), 'Required concept state missing'
    evidence={e['id']:e for e in value['evidence']}
    assert len(evidence)==len(value['evidence']), 'Duplicate evidence id'
    assert value['observation']['view_revision']==value['workspace']['view_revision'], 'Observation belongs to an old view'
    queue=value['queue'];current=queue['current_checkpoint_id']
    upcoming=queue['upcoming_checkpoint_ids'];done=queue['done_checkpoint_ids']
    assert not set(done)&set(upcoming) and current not in done+upcoming, 'Conflicting queue membership'
    assert set(done)=={i for i,s in states.items() if s['status']=='done'}, 'Done projection disagrees with checkpoint state'
    seen=set(done)|({current} if current else set())
    for identity in upcoming:
        assert set(definitions[identity]['depends_on'])<=seen, 'Upcoming queue violates dependencies'
        seen.add(identity)
    remaining=set(states)-set(done)-({current} if current else set())
    assert set(upcoming)==remaining, 'Queue loses an unfinished checkpoint'
    if current:
        assert states[current]['status'] in ['in_progress','blocked','awaiting_review','needs_recheck'], 'Current checkpoint is not active'
        assert all(states[d]['status']=='done' for d in definitions[current]['depends_on']), 'Dependencies incomplete'
    for identity,step in states.items():
        required={c['id'] for c in definitions[identity]['completion_criteria']}
        assert {c['criterion_id'] for c in step['criteria']}==required, 'Missing or extra completion criterion'
        assert len(step['criteria'])==len(required), 'Duplicate completion criterion'
        assert step['attempt_count']==len(step['visits']), 'Attempt count differs from visit history'
        for criterion in step['criteria']:
            assert all(e in evidence for e in criterion['evidence_ids']), 'Evidence reference not found'
            if criterion['state']=='satisfied':
                assert criterion['review_basis'] in ['reviewed_visual','adapter_verified'], 'Inference or self-report became verification'
                assert criterion['evidence_ids'], 'Satisfied criterion has no evidence'
                for ref in criterion['evidence_ids']:
                    e=evidence[ref]
                    assert e['review_status']=='accepted' and e['reviewed_by'], 'Evidence not reviewed'
                    assert e['checkpoint_id']==identity and e['visit_id'] in step['visits'], 'Evidence belongs to a different step visit'
                    assert e['workspace_id']==value['workspace']['id'], 'Evidence belongs to another workspace'
                    assert e['parameter_revision']==criterion['parameter_revision'], 'Evidence parameter revision mismatch'
        if step['status']=='done':
            assert all(c['state']=='satisfied' for c in step['criteria']), 'Bundled checkpoint completed partially'
            assert all(states[d]['status']=='done' for d in definitions[identity]['depends_on']), 'Done step lacks dependency completion'
        timing=step['timing']
        assert timing['tracking_active_ms']+timing['paused_ms']+timing['disconnected_ms']<=timing['wall_ms'], 'Timing intervals overlap'
        assert timing['valid_observation_ms']<=timing['tracking_active_ms'], 'Observation time exceeds active tracking'
    if value['mode']=='learner':
        assert not value['readiness']['operator_trial_override'], 'Operator override leaked into learner mode'
        if value['status']=='active':
            assert value['readiness']['required_concept_gate']=='passed', 'Active learner bypassed prerequisite gate'
            assert all(c['theory_check']=='passed' and c['assessment_run_ids'] for c in value['learner_state']['concepts']), 'Prerequisite pass lacks assessment evidence'
    if not value['synthetic']:
        assert all(not e['synthetic'] for e in evidence.values()), 'Synthetic evidence imported into a real session'
    if current and value['guidance']['state']=='current_step':
        assert value['guidance']['now_checkpoint_id']==current, 'Guidance targets a different checkpoint'
        assert value['guidance']['based_on_visit_id']==states[current]['current_visit_id'], 'Late guidance targets a different visit'
        assert value['guidance']['next_checkpoint_id']==(upcoming[0] if upcoming else None), 'Next guidance disagrees with queue'
    return True


check(example)
# Negative examples demonstrate meaningful contract failures, not factual vision checks.
mutations={
    'partial_completion':lambda v:v['steps'][1]['criteria'][1].update(state='unknown'),
    'self_report_promoted':lambda v:v['steps'][0]['criteria'][0].update(review_basis='self_report'),
    'cross_workspace_evidence':lambda v:v['evidence'][0].update(workspace_id='other-model'),
    'stale_visit_guidance':lambda v:v['guidance'].update(based_on_visit_id='old-visit'),
    'duplicate_checkpoint':lambda v:v['steps'][3].update(checkpoint_id=v['steps'][2]['checkpoint_id']),
    'concept_gate_bypass':lambda v:v.update(mode='learner'),
    'synthetic_real_evidence':lambda v:v.update(synthetic=False),
    'overlapping_timing':lambda v:v['steps'][2]['timing'].update(wall_ms=1000,tracking_active_ms=900,paused_ms=200),
    'missing_evidence':lambda v:v['steps'][0]['criteria'][0].update(evidence_ids=['missing']),
    'wrong_parameter_revision':lambda v:v['evidence'][0].update(parameter_revision=99),
    'wrong_view_revision':lambda v:v['observation'].update(view_revision=99),
}
for name,mutate in mutations.items():
    value=copy.deepcopy(example);mutate(value)
    try:check(value)
    except (AssertionError,ValidationError):
        pass
    else:raise AssertionError(f'Invalid example passed: {name}')
print(json.dumps({'status':'PASS','checkpoints':len(definition['checkpoints']),'blocks':len(definition['model']['blocks']),
    'connections':len(definition['model']['connections']),'valid_synthetic_projection':True,'rejected_invalid_scenarios':list(mutations),
    'live_simulink_or_model_calls':False},indent=2))
