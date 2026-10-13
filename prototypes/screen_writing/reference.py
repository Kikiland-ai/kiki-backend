"""v0.2 reference trust/ordering policy, with an injected renderer and frame broker.

No DOM, Simulink adapter or real rendering is implemented here. Production consumers
must port these checks and emit success acknowledgements only after actual delivery.
"""
from __future__ import annotations
import base64,copy,hashlib,io,json,math,uuid
from datetime import datetime
from pathlib import Path
from jsonschema import Draft202012Validator,FormatChecker,ValidationError
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
SCHEMA=json.loads((ROOT/'contracts/screen_writing.schema.json').read_text())
CATALOG={t['target_id']:t for t in json.loads((ROOT/'contracts/screen_writing_targets.json').read_text())['targets']}
VALIDATOR=Draft202012Validator(SCHEMA,format_checker=FormatChecker())

class Rejected(ValueError):
    pass

def require(condition,reason):
    if not condition:raise Rejected(reason)

def instant(value):return datetime.fromisoformat(value.replace('Z','+00:00'))
def region_inside(region):
    return region['x']+region['width']<=1+1e-12 and region['y']+region['height']<=1+1e-12

def active_context(context,runtime):
    require(runtime['session_status']=='active' and runtime['observation_status']=='available','inactive_session_or_observation')
    require(context==runtime['context'],'stale_context')

def validity(value,now,frame):
    created,expires=instant(value['created_at']),instant(value['expires_at'])
    require(created<=now<expires and 0<(expires-created).total_seconds()<=8,'expired_or_invalid_lifetime')
    received,admitted=instant(frame['received_at']),instant(frame['admitted_at'])
    require(received<=admitted<=created,'invalid_timestamp_authority_order')
    require(0<=(now-received).total_seconds()*1000<=value['max_frame_age_ms'],'stale_frame')

class FixtureBroker:
    """A test-only owner-bound ephemeral handle resolver with exact pixel verification."""
    def __init__(self,directory):self.directory=Path(directory).resolve()
    def fetch(self,handle,runtime,frame,now):
        record=runtime['frame_handles'].get(handle['handle_id'])
        require(record is not None,'unknown_frame_handle')
        require(record['owner_id']==runtime['owner_id'],'foreign_frame_handle_owner')
        require(record['frame_id']==frame['frame_id'] and record['expires_at']==handle['expires_at'],'foreign_frame_handle')
        require(now<instant(record['expires_at']),'expired_frame_handle')
        path=(self.directory/record['fixture_pixels_file']).resolve()
        require(path.is_relative_to(self.directory),'invalid_fixture_path')
        pixels=base64.b64decode(path.read_text(),validate=False)
        require(hashlib.sha256(pixels).hexdigest()==frame['sha256'] and len(pixels)==frame['byte_count'],'foreign_frame_pixels')
        with Image.open(io.BytesIO(pixels)) as image:
            require(image.format=='JPEG' and image.size==(frame['encoded_width'],frame['encoded_height']),'foreign_frame_dimensions')
            image.verify()
        return pixels

def validate_request(request,runtime,now,broker):
    VALIDATOR.validate(request)
    require(request['message_type']=='cue_request','wrong_message_type')
    active_context(request['context'],runtime)
    require(request['guidance_stream_id']==runtime['stream']['guidance_stream_id'],'foreign_stream')
    require(0<request['cue_sequence']<=runtime['stream']['last_issued_sequence'],'unissued_sequence')
    require(runtime['requests'].get(request['request_id'])==request,'foreign_or_modified_request')
    frame=request['frame']
    require(frame['observation_id']==runtime['active_observation_id'],'stale_observation')
    require(runtime['observations'].get(frame['observation_id'])==frame,'foreign_frame')
    require(frame['view_revision']==request['context']['view_revision'],'stale_frame_view')
    require(request['canonical_instruction']==runtime['canonical_instruction'],'foreign_instruction')
    validity(request['validity'],now,frame)
    ids=[t['target_id'] for t in request['requested_targets']]
    require(len(ids)==len(set(ids)),'duplicate_target_id')
    require(any(t['required_for_cue'] for t in request['requested_targets']),'missing_required_target')
    for target in request['requested_targets']:
        authored=CATALOG[target['target_id']]
        require(all(target[k]==authored[k] for k in ['semantic_label','kind','block_id','parameter_name']),'foreign_semantic_identity')
        criteria=target['criterion_ids']
        require(criteria and set(criteria)<=set(authored['criterion_ids']) and all(c.startswith(request['context']['checkpoint_id']+':') for c in criteria),'foreign_target_criterion')
    relations=request['relationships']
    require(len({r['relationship_id'] for r in relations})==len(relations),'duplicate_relationship_id')
    for relation in relations:
        require(relation['from_target_id'] in ids and relation['to_target_id'] in ids and relation['from_target_id']!=relation['to_target_id'],'foreign_relationship_target')
    return broker.fetch(request['frame_handle'],runtime,frame,now)

def anchor_xy(anchor,targets):
    target=targets.get(anchor['target_id'])
    require(target and target['status']=='resolved','operation_target_not_resolved')
    region=target['region']
    return [region['x']+anchor['u']*region['width'],region['y']+anchor['v']*region['height']]

def validate_packet(packet,runtime,now,broker):
    VALIDATOR.validate(packet)
    require(packet['message_type']=='resolved_packet','wrong_message_type')
    active_context(packet['context'],runtime)
    request=runtime['requests'].get(packet['request_id'])
    require(request is not None,'unknown_request')
    pixels=validate_request(request,runtime,now,broker)
    require(packet['frame']==request['frame'],'foreign_frame')
    require(packet['context']==request['context'] and packet['guidance_stream_id']==request['guidance_stream_id'] and packet['cue_sequence']==request['cue_sequence'],'foreign_request_binding')
    require(packet['validity']==request['validity'],'extended_or_changed_validity')
    require(packet['relationships']==request['relationships'],'foreign_relationship')
    require(packet['delivery']['surface']==request['requested_surface'],'foreign_delivery_surface')
    require(packet['fallback']['instruction']==request['canonical_instruction'],'foreign_instruction')
    requested={t['target_id']:t for t in request['requested_targets']}
    targets={t['target_id']:t for t in packet['resolved_targets']}
    require(len(targets)==len(packet['resolved_targets']),'duplicate_resolved_target_id')
    require(set(targets)==set(requested),'missing_or_foreign_target')
    for target in targets.values():
        if target['status']=='resolved':require(target['region'] is not None and target['method'] is not None and region_inside(target['region']),'invalid_resolved_region')
        else:require(target['region'] is None,'unresolved_target_has_geometry')
    unresolved=any(t['required_for_cue'] and targets[i]['status']!='resolved' for i,t in requested.items())
    if unresolved:
        require(not packet['operations'] and packet['fallback']['reason']=='unresolved_required_target','unresolved_required_target_operations')
        return {'status':'text_only','actual_surface':'guide_panel','text':request['canonical_instruction'],'operations':[],'pixels':pixels}
    require(packet['fallback']['reason']=='none','invalid_fallback_reason')
    require(bool(packet['operations']),'empty_resolved_operations')
    require(len({o['cue_id'] for o in packet['operations']})==len(packet['operations']),'duplicate_cue_id')
    relations={r['relationship_id']:r for r in request['relationships']}
    geometry=[]
    for operation in packet['operations']:
        kind=operation['kind']
        if kind in ['box','ellipse']:
            target=targets.get(operation['target_id']);require(target and target['status']=='resolved','operation_target_not_resolved');points=[]
            r=target['region'];points=[[r['x'],r['y']],[r['x']+r['width'],r['y']+r['height']]]
        elif kind in ['pointer','text']:points=[anchor_xy(operation['anchor'],targets)]
        else:
            relation=relations.get(operation['relationship_id']);require(relation is not None,'foreign_operation_relationship')
            anchors=[operation['from'],operation['to']] if kind=='arrow' else operation['anchors']
            require(anchors[0]['target_id']==relation['from_target_id'] and anchors[-1]['target_id']==relation['to_target_id'],'operation_relationship_endpoint_mismatch')
            require(all(a['target_id'] in [relation['from_target_id'],relation['to_target_id']] for a in anchors),'unrelated_polyline_anchor')
            points=[anchor_xy(a,targets) for a in anchors]
        require(all(0<=x<=1+1e-12 and 0<=y<=1+1e-12 for x,y in points),'out_of_frame_operation')
        geometry.extend(points)
    surface=packet['delivery']['surface']
    if surface=='captured_frame':
        preview=runtime.get('preview')
        require(preview and all(preview[k]==packet['frame'][k] for k in ['frame_id','sha256','encoded_width','encoded_height']),'foreign_preview_frame')
        require(packet['delivery']['adapter_binding_id'] is None and packet['delivery']['transform_revision'] is None,'unexpected_live_binding')
        transform=preview
    else:
        binding=packet['delivery']['adapter_binding_id'];cap=runtime.get('live_capabilities',{}).get(binding)
        require(cap is not None,'missing_live_adapter_capability')
        needed=['owner_id','workspace_id','capture_epoch','view_revision','transform_revision','source_to_surface','surface_bounds','expires_at','proof_ref','adapter_version','authorized_surface','frame_id','sha256','encoded_width','encoded_height']
        require(all(k in cap for k in needed),'incomplete_live_adapter_proof')
        require(cap['owner_id']==runtime['owner_id'] and cap['authorized_surface']=='live_workspace','foreign_live_adapter_owner')
        require(now<instant(cap['expires_at']),'unverified_or_expired_live_adapter')
        proof=runtime.get('adapter_proofs',{}).get(cap['proof_ref'])
        require(proof is not None,'missing_live_integration_proof')
        require(all(k in proof for k in ['binding_id','owner_id','workspace_id','adapter_version','verified_at','expires_at','test_report_sha256','invalidation_events','source_coordinate_space','destination_coordinate_space']),'incomplete_live_integration_proof')
        require(proof['binding_id']==binding and proof['owner_id']==runtime['owner_id'] and proof['workspace_id']==packet['context']['workspace_id'] and proof['adapter_version']==cap['adapter_version'],'foreign_live_integration_proof')
        require(instant(proof['verified_at'])<=now<instant(proof['expires_at']) and len(proof['test_report_sha256'])==64,'expired_or_invalid_live_proof')
        require(set(['scroll','zoom','resize','canvas_pan','modal_change','layout_change'])<=set(proof['invalidation_events']),'incomplete_invalidation_capability')
        require(proof['source_coordinate_space']=='normalized_encoded_frame' and proof['destination_coordinate_space']=='live_workspace_css','foreign_live_coordinate_space')
        require(all(cap[k]==packet['context'][k] for k in ['workspace_id','capture_epoch','view_revision']),'stale_live_adapter_view')
        require(cap['transform_revision']==packet['delivery']['transform_revision'],'stale_live_transform')
        require(all(cap[k]==packet['frame'][k] for k in ['frame_id','sha256','encoded_width','encoded_height']),'foreign_live_transform_frame')
        transform=cap
    matrix=transform['source_to_surface'];bounds=transform['surface_bounds']
    require(len(matrix)==6 and all(isinstance(v,(float,int)) and math.isfinite(v) for v in matrix),'invalid_transform')
    require(abs(matrix[0]*matrix[4]-matrix[1]*matrix[3])>1e-12,'singular_transform')
    # The entire encoded frame must map into the adapter/preview's verified clipping bounds.
    for x,y in [[0,0],[1,0],[0,1],[1,1]]+geometry:
        dx=matrix[0]*x+matrix[1]*y+matrix[2];dy=matrix[3]*x+matrix[4]*y+matrix[5]
        require(bounds['x']-1e-9<=dx<=bounds['x']+bounds['width']+1e-9 and bounds['y']-1e-9<=dy<=bounds['y']+bounds['height']+1e-9,'transform_out_of_bounds')
    return {'status':'preview_rendered' if surface=='captured_frame' else 'live_rendered','actual_surface':surface,'text':None,'operations':packet['operations'],'pixels':pixels}

class ReferenceConsumer:
    """One authoritative stream, full replacements and cancellation fences.

    The renderer is injected. The acceptance suite uses a fake; real success must
    be emitted only after an atomic real compositor commit and a final context check.
    """
    def __init__(self,broker,renderer):
        self.broker=broker;self.renderer=renderer;self.high_water=0;self.seen=set();self.active_packet=None;self.cancelled_packet=None;self.active_surface='none';self.cancelled_surface='none'
    def ack(self,message,runtime,now,status,reason,surface='none'):
        packet=message if message['message_type']=='resolved_packet' else (self.active_packet or self.cancelled_packet)
        value={'schema':'screen-writing/v0.2','message_type':'delivery_ack','ack_id':str(uuid.uuid4()),
          'request_id':packet['request_id'] if packet else None,'packet_id':packet['packet_id'] if packet else None,
          'cancel_id':message.get('cancel_id'),'guidance_stream_id':message['guidance_stream_id'],'cue_sequence':message['cue_sequence'],
          'context':copy.deepcopy(message['context']),'packet_context':copy.deepcopy(packet['context']) if packet else None,'actual_surface':surface,'delivered_at':now.isoformat(),'timestamp_authority':'consumer_clock',
          'status':status,'reason':reason,'adapter_binding_id':packet['delivery']['adapter_binding_id'] if packet and surface=='live_workspace' else None,
          'transform_revision':packet['delivery']['transform_revision'] if packet and surface=='live_workspace' else None}
        VALIDATOR.validate(value);return value
    def sync(self,runtime,now):
        # Trusted local invalidation clears immediately, before any cancellation round trip.
        packet=self.active_packet
        if packet and (packet['context']!=runtime['context'] or runtime['session_status']!='active' or runtime['observation_status']!='available' or
                packet['frame']['observation_id']!=runtime['active_observation_id'] or now>=instant(packet['validity']['expires_at'])):
            self.renderer.clear();self.cancelled_packet=self.active_packet;self.cancelled_surface=self.active_surface;self.active_packet=None;self.active_surface='none'
            self.high_water=max(self.high_water,runtime['stream'].get('cancelled_through_sequence',0))
    def consume(self,message,runtime,now):
        clock=now if callable(now) else lambda:now
        now=clock()
        self.sync(runtime,now)
        shaped=False
        try:
            VALIDATOR.validate(message);shaped=True
            identity=message.get('packet_id') or message.get('cancel_id')
            require(identity is not None,'wrong_message_type')
            require(identity not in self.seen,'duplicate_message_id')
            require(message['guidance_stream_id']==runtime['stream']['guidance_stream_id'],'foreign_stream')
            require(self.high_water<message['cue_sequence']<=runtime['stream']['last_issued_sequence'],'out_of_order_or_cancelled')
            require(len(self.seen)<500,'stream_budget_exhausted')
            self.seen.add(identity)
            if message['message_type']=='cancel':
                require(message['context']==runtime['context'],'stale_context')
                require(instant(message['issued_at'])<=now,'future_cancellation')
                self.high_water=message['cue_sequence']
                ack=self.ack(message,runtime,now,'cancelled',message['reason'],self.active_surface if self.active_packet else self.cancelled_surface)
                self.renderer.clear();self.active_packet=None;self.cancelled_packet=None;self.active_surface='none';self.cancelled_surface='none';return ack
            plan=validate_packet(message,runtime,now,self.broker)
            # Sequence reservation prevents failures or asynchronous supersession from reviving an older message.
            self.high_water=message['cue_sequence']
            self.renderer.replace_complete_layer(plan)
            now=clock()
            active_context(message['context'],runtime)
            require(now<instant(message['validity']['expires_at']),'expired_before_commit')
            self.active_packet=copy.deepcopy(message);self.active_surface=plan['actual_surface']
            return self.ack(message,runtime,now,plan['status'],'unresolved_required_target' if plan['status']=='text_only' else 'rendered',plan['actual_surface'])
        except (Rejected,ValidationError) as error:
            # No fallback text is delivered on rejection. Foreign/invalid packets cannot clear a valid current layer.
            reason=str(error) if isinstance(error,Rejected) else 'schema_invalid'
            if not shaped:raise Rejected('schema_invalid') from error
            if reason not in ['duplicate_message_id','out_of_order_or_cancelled'] and message.get('packet_id') in self.seen and message.get('cue_sequence')==self.high_water:
                self.renderer.clear();self.active_packet=None;self.active_surface='none'
            if message.get('message_type')=='resolved_packet':return self.ack(message,runtime,now,'rejected',reason)
            raise
