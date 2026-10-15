"""Bounded committed projection; no model prose or auxiliary work can advance it."""
import copy

def decision_summary(value):
    rows=[*value['criteria'],*value['action_findings']]
    for status,prefix in (('mismatch','Check this: '),('match','Visible: '),('unknown','Not established: ')):
        row=next((row for row in rows if row['status']==status and row['evidence'].strip()),None)
        if row:return prefix+row['evidence']
    return 'The relevant settings or connections are not established in this view.'

def committed_projection(state):
    fields=('schema','lab_session_id','experiment_id','revision','status','progression_mode','current_visit_id',
            'workspace','queue','guidance','observation','auto_tracking','procedure_tracking','procedure_history')
    value={key:copy.deepcopy(state[key]) for key in fields if key in state}
    steps=state['steps']
    def step(item):
        result={key:copy.deepcopy(item[key]) for key in ('checkpoint_id','status','current_visit_id','criteria','timing','attempt_count') if key in item}
        return result
    value['steps']={key:step(item) for key,item in steps.items()} if isinstance(steps,dict) else [step(item) for item in steps]
    value['runtime']={key:copy.deepcopy(state['runtime'][key]) for key in ('analysis_attempts','analysis_status','analysis_error','retry_at_ms','retry_after_ms','last_analysis_timing','candidate') if key in state['runtime']}
    value['projection']='committed-decision/v1'
    return value
