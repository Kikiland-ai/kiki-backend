"""Run v0.2 acceptance checks with synthetic pixels, geometry and a fake compositor.

This verifies trust/ordering policy, not target recognition, actual cue delivery or
Simulink overlay integration. Success ACKs here belong only to the test simulation.
"""
import copy,json,sys
from datetime import datetime,timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from prototypes.screen_writing.reference import VALIDATOR,FixtureBroker,ReferenceConsumer,Rejected,validate_request
P=ROOT/'docs/architecture/examples/screen-writing/v0.2'
(P/'invalid').mkdir(exist_ok=True)
load=lambda name:json.loads((P/name).read_text())
BASE=load('trusted.synthetic.runtime.json');PACKET=load('single.packet.json')
NOW=datetime.fromisoformat('2026-10-14T00:30:02+05:30')
VALIDATOR.check_schema(VALIDATOR.schema)

class FakeRenderer:
    def __init__(self):self.layer=None;self.clears=0;self.after_commit=None
    def replace_complete_layer(self,plan):
        self.layer={'text':plan['text'],'operations':copy.deepcopy(plan['operations'])}
        if self.after_commit:self.after_commit()
    def clear(self):self.layer=None;self.clears+=1

def fresh(runtime=None):
    r=copy.deepcopy(runtime or BASE);renderer=FakeRenderer()
    return r,renderer,ReferenceConsumer(FixtureBroker(P),renderer)

def consume(message,runtime=None):
    r,renderer,c=fresh(runtime);ack=c.consume(copy.deepcopy(message),r,NOW);return ack,renderer,c

passed=[];cases=[]
def record(name,expected):passed.append(name);cases.append({'name':name,'expected':expected})

ack,renderer,c=consume(PACKET)
assert ack['status']=='preview_rendered' and renderer.layer['operations'] and renderer.layer['text'] is None
record('valid_single_target','preview_rendered')

r=copy.deepcopy(BASE);mr=load('multi.request.json');mp=load('multi.packet.json')
r.update(context=mr['context'],canonical_instruction=mr['canonical_instruction'],requests={mr['request_id']:mr})
ack,renderer,c=consume(mp,r);assert ack['status']=='preview_rendered'
record('multi_target_comparison','preview_rendered')
mu=copy.deepcopy(mp);mu['packet_id']='synthetic-multi-unresolved';mu['resolved_targets'][1].update(status='unresolved',region=None,reason='Synthetic missing trace.');mu['operations']=[];mu['fallback']['reason']='unresolved_required_target'
(P/'multi-unresolved.packet.json').write_text(json.dumps(mu,indent=2)+'\n')
ack,renderer,c=consume(mu,r);assert ack['status']=='text_only' and not renderer.layer['operations'];record('one_required_multi_target_unresolved','text_only')

ack,renderer,c=consume(load('unresolved.packet.json'))
assert ack['status']=='text_only' and not renderer.layer['operations'] and renderer.layer['text']==BASE['canonical_instruction']
record('unresolved_valid_context','text_only')
stale=load('unresolved.packet.json');stale['context']['view_revision']=3;ack,renderer,c=consume(stale);assert ack['status']=='rejected' and renderer.layer is None;record('stale_unresolved_fallback','discarded_completely')

mutations={
 'stale_visit':(lambda p:p['context'].update(visit_id='old-visit'),'stale_context'),
 'stale_view':(lambda p:p['context'].update(view_revision=3),'stale_context'),
 'stale_condition':(lambda p:p['context'].update(condition='phase_fault'),'stale_context'),
 'stale_workspace':(lambda p:p['context'].update(workspace_id='other-model'),'stale_context'),
 'stale_parameter_revision':(lambda p:p['context'].update(parameter_revision=1),'stale_context'),
 'foreign_frame_id':(lambda p:p['frame'].update(frame_id='different-frame'),'foreign_frame'),
 'foreign_frame_hash':(lambda p:p['frame'].update(sha256='f'*64),'foreign_frame'),
 'foreign_frame_dimensions':(lambda p:p['frame'].update(encoded_width=100),'foreign_frame'),
 'duplicate_cue_ids':(lambda p:p['operations'].append(copy.deepcopy(p['operations'][0])),'duplicate_cue_id'),
 'duplicate_resolved_target':(lambda p:p['resolved_targets'].append(copy.deepcopy(p['resolved_targets'][0])),'duplicate_resolved_target_id'),
 'out_of_frame_region':(lambda p:p['resolved_targets'][0]['region'].update(x=.9,width=.3),'invalid_resolved_region'),
 'unrelated_operation_target':(lambda p:p['operations'][0].update(target_id='carrier.frequency'),'operation_target_not_resolved'),
 'foreign_fallback_instruction':(lambda p:p['fallback'].update(instruction='An obsolete instruction.'),'foreign_instruction'),
 'extended_expiry':(lambda p:p['validity'].update(expires_at='2026-10-14T00:30:12+05:30'),'extended_or_changed_validity'),
 'unresolved_with_operations':(lambda p:p['resolved_targets'][0].update(status='unresolved',region=None),'unresolved_required_target_operations')}
for name,(mutate,reason) in mutations.items():
    p=copy.deepcopy(PACKET);mutate(p)
    (P/'invalid'/f'{name}.packet.json').write_text(json.dumps(p,indent=2)+'\n')
    ack,renderer,c=consume(p)
    assert ack['status']=='rejected' and ack['reason']==reason,(name,ack)
    assert renderer.layer is None,(name,'Rejection displayed stale fallback')
    record(name,'rejected:'+reason)

# Foreign bytes cannot be trusted merely because packet/request metadata agree.
r=copy.deepcopy(BASE);r['frame_handles']['synthetic-handle-7']['owner_id']='foreign-owner'
ack,renderer,c=consume(PACKET,r);assert ack['reason']=='foreign_frame_handle_owner';record('foreign_handle_owner','rejected')
r=copy.deepcopy(BASE);r['preview']['frame_id']='newer-preview-frame'
ack,renderer,c=consume(PACKET,r);assert ack['reason']=='foreign_preview_frame';record('different_mounted_preview','rejected')
r=copy.deepcopy(BASE);r['active_observation_id']='new-admitted-observation'
ack,renderer,c=consume(PACKET,r);assert ack['reason']=='stale_observation';record('stale_observation','rejected')

# A second packet is full replacement; older packets and duplicate IDs cannot resurrect a layer.
r,renderer,c=fresh();p2=copy.deepcopy(PACKET);p2.update(packet_id='synthetic-packet-2',request_id='synthetic-request-2',cue_sequence=2)
r2=copy.deepcopy(r['requests']['synthetic-request-1']);r2.update(request_id=p2['request_id'],cue_sequence=2);r['requests'][r2['request_id']]=r2
assert c.consume(p2,r,NOW)['status']=='preview_rendered';layer=copy.deepcopy(renderer.layer)
assert c.consume(PACKET,r,NOW)['reason']=='out_of_order_or_cancelled' and renderer.layer==layer
assert c.consume(p2,r,NOW)['reason']=='duplicate_message_id' and renderer.layer==layer
record('out_of_order_delivery','rejected_without_clearing_current_layer');record('duplicate_packet_id','deduplicated')

# Immediate local view invalidation + an ordered cancellation fences all older work.
r,renderer,c=fresh();assert c.consume(PACKET,r,NOW)['status']=='preview_rendered'
cancel=load('view.cancel.json');r['context']=copy.deepcopy(cancel['context'])
ack=c.consume(cancel,r,NOW+timedelta(seconds=1));assert ack['status']=='cancelled' and ack['packet_id']==PACKET['packet_id'] and ack['actual_surface']=='captured_frame' and ack['packet_context']['view_revision']==4 and renderer.layer is None
assert c.consume(PACKET,r,NOW+timedelta(seconds=1))['status']=='rejected' and renderer.layer is None
record('view_cancellation','cancelled_then_old_packet_rejected')
# A new-context request after the cancellation is allowed; fencing must not kill newer work.
r['stream']['last_issued_sequence']=3
newr=copy.deepcopy(BASE['requests']['synthetic-request-1']);newr.update(request_id='synthetic-request-3',cue_sequence=3,context=copy.deepcopy(r['context']))
newr['frame']['view_revision']=5;newr['frame']['observation_id']='synthetic-observation-8';newr['frame']['frame_id']='synthetic-frame-8'
r['requests'][newr['request_id']]=newr;r['active_observation_id']=newr['frame']['observation_id'];r['observations'][newr['frame']['observation_id']]=newr['frame']
r['frame_handles']['synthetic-handle-7']['frame_id']=newr['frame']['frame_id'];r['preview']['frame_id']=newr['frame']['frame_id']
np=copy.deepcopy(PACKET);np.update(packet_id='synthetic-packet-3',request_id=newr['request_id'],cue_sequence=3,context=newr['context'],frame=newr['frame'])
assert c.consume(np,r,NOW+timedelta(seconds=1))['status']=='preview_rendered';record('new_context_after_cancellation','preview_rendered')

for status in ['paused','disconnected']:
    r,renderer,c=fresh();c.consume(PACKET,r,NOW);r['session_status']=status;c.sync(r,NOW)
    assert renderer.layer is None and c.consume(load('unresolved.packet.json'),r,NOW)['status']=='rejected'
    record(status+'_clears_layer','cleared_no_fallback')

# Live approval comes from a trusted, owner/view/frame-bound capability + transform, never a packet flag.
r=copy.deepcopy(BASE);live=copy.deepcopy(PACKET);live['delivery'].update(surface='live_workspace',adapter_binding_id='synthetic-adapter',transform_revision=2)
r['requests']['synthetic-request-1']['requested_surface']='live_workspace'
ack,renderer,c=consume(live,r);assert ack['reason']=='missing_live_adapter_capability';record('missing_live_adapter','rejected')
r['live_capabilities']['synthetic-adapter']={'verified':True}
ack,renderer,c=consume(live,r);assert ack['reason']=='incomplete_live_adapter_proof';record('boolean_adapter_placeholder','rejected')
r['live_capabilities']['synthetic-adapter']={**copy.deepcopy(r['preview']),'owner_id':r['owner_id'],'workspace_id':r['context']['workspace_id'],
 'capture_epoch':1,'view_revision':4,'transform_revision':2,'expires_at':'2026-10-14T00:30:09+05:30','proof_ref':'synthetic-integration-proof-only',
 'adapter_version':'synthetic-adapter/v1','authorized_surface':'live_workspace'}
ack,renderer,c=consume(live,r);assert ack['reason']=='missing_live_integration_proof';record('missing_trusted_integration_proof','rejected')
r['adapter_proofs']={'synthetic-integration-proof-only':{'binding_id':'synthetic-adapter','owner_id':r['owner_id'],'workspace_id':r['context']['workspace_id'],'adapter_version':'synthetic-adapter/v1','verified_at':'2026-10-14T00:30:00+05:30','expires_at':'2026-10-14T00:30:09+05:30','test_report_sha256':'f'*64,'invalidation_events':['scroll','zoom','resize','canvas_pan','modal_change','layout_change'],'source_coordinate_space':'normalized_encoded_frame','destination_coordinate_space':'live_workspace_css'}}
ack,renderer,c=consume(live,r);assert ack['status']=='live_rendered';record('complete_synthetic_live_capability','simulated_live_rendered_only')
saved=copy.deepcopy(r)
r['adapter_proofs']['synthetic-integration-proof-only']['expires_at']='2026-10-14T00:30:01+05:30'
ack,renderer,c=consume(live,r);assert ack['reason']=='expired_or_invalid_live_proof';record('expired_live_integration_proof','rejected')
r=copy.deepcopy(saved);r['live_capabilities']['synthetic-adapter']['source_to_surface']=[960,0,1000,0,540,20]
ack,renderer,c=consume(live,r);assert ack['reason']=='transform_out_of_bounds';record('out_of_bounds_live_transform','rejected')
r=copy.deepcopy(saved);r['live_capabilities']['synthetic-adapter']['view_revision']=3
ack,renderer,c=consume(live,r);assert ack['reason']=='stale_live_adapter_view';record('stale_live_transform','rejected')

r,renderer,c=fresh();clock=[NOW];renderer.after_commit=lambda:clock.__setitem__(0,NOW+timedelta(seconds=10))
ack=c.consume(PACKET,r,lambda:clock[0]);assert ack['status']=='rejected' and renderer.layer is None;record('expiry_during_delivery','cleared_rejected')

# Cross-target relationships and malformed v0.1 packets are not accepted.
r=copy.deepcopy(BASE);mr=load('multi.request.json');mp=load('multi.packet.json');r.update(context=mr['context'],canonical_instruction=mr['canonical_instruction'],requests={mr['request_id']:mr})
mp['operations'][0]['to']['target_id']='message.frequency';ack,renderer,c=consume(mp,r)
assert ack['reason']=='operation_relationship_endpoint_mismatch';record('unrelated_comparison_endpoint','rejected')
try:consume({'schema':'screen-writing/v0.1','packet_id':'old'})
except Rejected:record('v0.1_incompatible','transport_rejection')
else:raise AssertionError('v0.1 accepted')

for name in ['single.request.json','single.packet.json','multi.request.json','multi.packet.json','unresolved.packet.json','view.cancel.json','preview.ack.json']:VALIDATOR.validate(load(name))
report={'status':'PASS','schema':'screen-writing/v0.2','acceptance_count':len(passed),'cases':cases,
 'actual_renderer':'not_implemented','live_simulink_overlay_verified':False,'synthetic_geometry':True}
(P/'acceptance-manifest.json').write_text(json.dumps({'schema':'screen-writing-acceptance/v0.2','synthetic':True,'cases':cases},indent=2)+'\n')
(ROOT/'work').mkdir(exist_ok=True)
(ROOT/'work/screen-writing-v02-check.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
