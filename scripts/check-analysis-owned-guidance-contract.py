"""Contract proposal checks only. No provider, tracker mutation, consumer or renderer.
Run: python scripts/check-analysis-owned-guidance-contract.py
"""
import base64,copy,hashlib,io,json,sys,math
from datetime import datetime
from pathlib import Path
from jsonschema import Draft202012Validator,FormatChecker,ValidationError
from referencing import Registry,Resource
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'docs/architecture/examples/analysis-owned-guidance/v0.1'
load=lambda name:json.loads((P/name).read_text())
legacy=json.loads((ROOT/'contracts/screen_writing.schema.json').read_text())
model_schema=json.loads((ROOT/'contracts/lab_observer_drawing.v1.schema.json').read_text())
schema=json.loads((ROOT/'contracts/analysis_owned_guidance.v0_1.schema.json').read_text())
registry=Registry().with_resource(legacy['$id'],Resource.from_contents(legacy))
MV=Draft202012Validator(model_schema,registry=registry,format_checker=FormatChecker())
CV=Draft202012Validator(schema,registry=registry,format_checker=FormatChecker())
for value in (legacy,model_schema,schema):Draft202012Validator.check_schema(value)

def require(value,reason):
 if not value:raise ValueError(reason)
def unique(values,key,reason):
 ids=[v[key] for v in values];require(len(ids)==len(set(ids)),reason);return set(ids)
def strict(raw):
 def pairs(items):
  value={}
  for k,v in items:require(k not in value,'duplicate_json_key');value[k]=v
  return value
 def constant(value):raise ValueError('nonfinite_json_number')
 def finite(value):
  parsed=float(value);require(math.isfinite(parsed),'nonfinite_json_number');return parsed
 return json.loads(raw,object_pairs_hook=pairs,parse_constant=constant,parse_float=finite)
def instant(value):return datetime.fromisoformat(value.replace('Z','+00:00'))
def check_region(region):require(region['x']+region['width']<=1 and region['y']+region['height']<=1,'out_of_frame_region')
def mark_targets(mark):
 if mark['kind'] in ('box','ellipse'):return [mark['target_id']]
 if mark['kind']=='text':return [mark['anchor']['target_id']]
 return [mark['from']['target_id'],mark['to']['target_id']]
def accessible_label(mark,action):
 if mark['kind']=='arrow':
  rel=next(r for r in action['relationships'] if r['relationship_id']==mark['relationship_id'])
  return {'compares_with':'Compare the indicated targets.','connects_to':'Connect the indicated targets.','influences':'Show the indicated relationship.'}[rel['kind']]
 target=mark['target_id'] if mark['kind'] in ('box','ellipse') else mark['anchor']['target_id']
 return action['target_labels'][target]
def validate_model(model,runtime,finish='STOP'):
 require(finish=='STOP','missing_provider_stop');MV.validate(model)
 require(unique(model['criteria'],'criterion_id','duplicate_criterion')==set(runtime['expected_criterion_ids']),'foreign_or_missing_criteria')
 require(unique(model['action_findings'],'action_id','duplicate_finding')==set(runtime['expected_action_ids']),'foreign_or_missing_action_findings')
 unique(model['screen_guidance'],'action_id','duplicate_candidate')
 eligible={a['action_id']:a for a in runtime['eligible_actions']}
 for c in model['screen_guidance']:
  require(c['action_id'] in eligible,'ineligible_action');a=eligible[c['action_id']]
  targets=unique(c['targets'],'target_id','duplicate_target');unique(c['marks'],'cue_id','duplicate_cue')
  if c['mode']=='none':continue
  require(targets==set(a['required_target_ids']),'foreign_or_missing_targets')
  for t in c['targets']:
   if t['region'] is not None:check_region(t['region'])
  for mark in c['marks']:
   require(set(mark_targets(mark))<=targets,'unrelated_operation_target')
   if mark['kind']=='text':require(mark['text_ref'] in a['overlay_texts'],'foreign_text_reference')
   if mark['kind']=='arrow':
    rel=next((v for v in a['relationships'] if v['relationship_id']==mark['relationship_id']),None)
    require(rel is not None and mark['from']['target_id']==rel['from_target_id'] and mark['to']['target_id']==rel['to_target_id'],'foreign_relationship')
 return model

def validate_commit(value,runtime,model):
 CV.validate(value);require(value['message_type']=='committed_guidance','wrong_message_type');validate_model(model,runtime,runtime.get('provider_finish_reason','STOP'))
 require(runtime['session_status']=='active' and runtime['observation_status']=='available','inactive_context')
 require(value['context']==runtime['current_context'],'stale_context');require(value['admitted_context']==runtime['admitted_context'],'foreign_admission')
 require(value['action_id']==runtime['current_action_id'],'stale_action')
 require(value['analysis_request_id']==runtime['analysis_request_id'] and value['guidance_stream_id']==runtime['guidance_stream_id'],'foreign_request_or_stream')
 require(value['cue_sequence']>runtime['last_cue_sequence'],'older_or_cancelled_sequence')
 require(value['frame']==runtime['frame'] and value['frame_handle']==runtime['frame_handle'],'foreign_frame_provenance')
 require(value['source_binding']==runtime['source_binding'],'foreign_source_binding')
 for key in ('lab_session_id','experiment_id','workspace_id','capture_epoch','view_revision','parameter_revision','condition'):
  require(value['context'][key]==value['admitted_context'][key],'invalidated_source_context')
 require(value['frame']['view_revision']==value['context']['view_revision'],'foreign_frame_view')
 require(len(json.dumps(value).encode())<=runtime['max_payload_bytes'],'oversized_payload')
 valid=value['validity'];created,expires=instant(valid['created_at']),instant(valid['expires_at']);now=instant(runtime['now']);received=instant(value['frame']['received_at']);admitted=instant(value['frame']['admitted_at'])
 require(received<=admitted<=created<=now<expires,'invalid_or_expired_timestamp')
 require((expires-created).total_seconds()<=8 and (expires-received).total_seconds()*1000<=valid['max_frame_age_ms'] and expires<=instant(value['frame_handle']['expires_at']),'extended_expiry')
 require((now-received).total_seconds()*1000<=valid['max_frame_age_ms'],'old_frame')
 a=next(a for a in runtime['eligible_actions'] if a['action_id']==value['action_id']);c=next((c for c in model['screen_guidance'] if c['action_id']==value['action_id']),None)
 expected_mode=c['mode'] if c else 'none';require(value['outcome']==expected_mode,'wrong_candidate_selection')
 require(value['teaching_intent']==a['teaching_intent'],'foreign_teaching_intent')
 if value['outcome']=='none':
  require(value['packet'] is None and value['reason']==('model_declined' if c else 'no_matching_candidate'),'invalid_no_cue');return 'clear_only'
 require(value['target_criteria']==[{'target_id':t,'criterion_ids':a['subcriteria'][t]} for t in a['required_target_ids']],'foreign_target_criteria')
 p=value['packet'];require(p['context']==value['context'] and p['frame']==value['frame'] and p['validity']==valid,'foreign_packet_context')
 require(p['request_id']==value['analysis_request_id'] and p['guidance_stream_id']==value['guidance_stream_id'] and p['cue_sequence']==value['cue_sequence'],'foreign_packet_identifiers')
 require(p['packet_id'] not in runtime.get('seen_packet_ids',[]),'duplicate_packet_id')
 require(p['fallback']['instruction']==a['canonical_instruction'] and p['fallback']['reason']==value['reason'],'foreign_canonical_text')
 require(p['relationships']==a['relationships'],'foreign_relationship')
 require(len(p['resolved_targets'])==len(c['targets']),'missing_resolved_target');unique(p['resolved_targets'],'target_id','duplicate_resolved_target');unique(p['operations'],'cue_id','duplicate_cue')
 require(p['delivery']['surface']==value['source_binding']['surface'],'foreign_delivery_surface')
 if p['delivery']['surface']=='live_workspace':
  record=runtime.get('trusted_live_bindings',{}).get(value['source_binding']['binding_id'])
  require(isinstance(record,dict) and record.get('binding_revision')==value['source_binding']['binding_revision'] and record.get('transform_revision')==value['source_binding']['transform_revision'] and record.get('verified_frame')==value['frame'] and record.get('owner_id')==runtime.get('owner_id') and record.get('proof_kind')=='native_capture_handle_and_pixel_match' and p['delivery']['adapter_binding_id']==value['source_binding']['binding_id'] and p['delivery']['transform_revision']==value['source_binding']['transform_revision'],'unverified_live_binding')
 else:require(p['delivery']['adapter_binding_id'] is None and p['delivery']['transform_revision'] is None,'invalid_preview_transform')
 targets={t['target_id']:t for t in c['targets']}
 for t in p['resolved_targets']:
  require(t['target_id'] in targets and all(t[k]==targets[t['target_id']][k] for k in ('status','region')) and t['method']=='model_vision','relabeled_geometry')
 require(len(p['operations'])==len(c['marks']),'changed_marks')
 expected_text=[]
 for mark,operation in zip(c['marks'],p['operations']):
  expected=copy.deepcopy(mark);expected.update(meaning='lab',accessible_label=accessible_label(mark,a))
  if expected['kind']=='text':
   expected['text']=a['overlay_texts'][expected.pop('text_ref')];expected_text.append({'cue_id':mark['cue_id'],'text_ref':mark['text_ref']})
  require(operation==expected,'changed_operation_or_note')
 require(value['text_bindings']==expected_text,'foreign_text_binding')
 return value['outcome']

def validate_cancel(value,runtime):
 CV.validate(value);require(value['message_type']=='cancel','wrong_cancel_type')
 require(value['guidance_stream_id']==runtime['guidance_stream_id'],'foreign_stream')
 require(value['context']==runtime['current_context'],'stale_cancel_context')
 require(value['cue_sequence']>runtime['last_cue_sequence'],'older_or_cancelled_sequence')
 require(value['cancel_id'] not in runtime.get('seen_cancel_ids',[]),'duplicate_cancel_id')
 require(instant(value['issued_at'])<=instant(runtime['now']),'future_cancel');return 'clear_only'

cases=[]
def accept(name,action,expected=None):
 value=action();require(expected is None or value==expected,'unexpected_fixture_outcome');cases.append({'name':name,'outcome':'accepted','effect':value if isinstance(value,str) else 'validated_model'})
def reject(name,action):
 try:action()
 except (ValueError,KeyError,ValidationError) as error:cases.append({'name':name,'outcome':'rejected','reason':str(error).splitlines()[0][:160]});return
 raise AssertionError('Invalid fixture accepted: '+name)
def changed(value,path,replacement):
 value=copy.deepcopy(value);cursor=value
 for part in path[:-1]:cursor=cursor[part]
 cursor[path[-1]]=replacement;return value

if __name__=='__main__':
 fixture_manifest=load('manifest.json')
 for name,expected in fixture_manifest['files_sha256'].items():require(hashlib.sha256((P/name).read_bytes()).hexdigest()==expected,'fixture_manifest_mismatch')
 r=load('trusted.single.json');m=load('model.single.json');p=load('committed.single.json')
 for name in ('single','comparison','action-advance'):
  value=load('input.'+name+'.json');CV.validate(value);require(value['current_action_id']==value['eligible_actions'][0]['action_id'],'input_action_order');cases.append({'name':'trusted_input_'+name,'outcome':'accepted','effect':'validated_input'})
 pixels=base64.b64decode((P/'frame.jpeg.b64').read_text());image=Image.open(io.BytesIO(pixels));require(hashlib.sha256(pixels).hexdigest()==r['frame']['sha256'] and len(pixels)==r['frame']['byte_count'] and image.size==(r['frame']['encoded_width'],r['frame']['encoded_height']),'fixture_pixels_mismatch')
 for name in ('single','text-only','none','declined','action-advance','comparison','multi-unresolved'):
  runtime=load('trusted.action-advance.json' if name=='action-advance' else 'trusted.comparison.json' if name in ('comparison','multi-unresolved') else 'trusted.single.json')
  model=strict((P/('model.'+name+'.json')).read_text());packet=load('committed.'+name+'.json')
  accept(name,lambda runtime=runtime,model=model,packet=packet:validate_commit(packet,runtime,model),packet['outcome'] if packet['outcome']!='none' else 'clear_only')
 accept('advance_without_successor_clears',lambda:validate_commit(load('committed.no-matching-candidate.json'),load('trusted.action-advance.json'),m),'clear_only')
 for label,path,value in [('stale_view',('context','view_revision'),5),('stale_visit',('context','visit_id'),'other'),('stale_condition',('context','condition'),'phase_fault'),('stale_parameter',('context','parameter_revision'),3),('foreign_frame',('frame','frame_id'),'foreign'),('foreign_hash',('frame','sha256'),'0'*64),('wrong_dimensions',('frame','encoded_width'),97),('foreign_source_binding',('source_binding','binding_id'),'foreign'),('wrong_action',('action_id',),'CP-DSB-03/carrier-settings'),('old_sequence',('cue_sequence',),1),('foreign_note',('packet','operations',1,'text'),'Invented instruction.'),('unrelated_operation',('packet','operations',0,'target_id'),'carrier.frequency')]:
  runtime={**r,'last_cue_sequence':1} if label=='old_sequence' else r
  reject(label,lambda path=path,value=value,runtime=runtime:validate_commit(changed(p,path,value),runtime,m))
 reject('stale_unresolved_has_no_text_fallback',lambda:validate_commit(changed(load('committed.text-only.json'),('context','view_revision'),5),r,load('model.text-only.json')))
 reject('duplicate_packet_id',lambda:validate_commit(p,{**r,'seen_packet_ids':[p['packet']['packet_id']]},m))
 reject('inactive_session',lambda:validate_commit(p,{**r,'session_status':'paused'},m))
 reject('expired_packet',lambda:validate_commit(p,{**r,'now':'2026-10-15T00:00:10Z'},m))
 reject('out_of_frame_region',lambda:validate_model(changed(m,('screen_guidance',0,'targets',0,'region','x'),.9),r))
 duplicate=copy.deepcopy(m);duplicate['screen_guidance'][0]['marks'][1]['cue_id']=duplicate['screen_guidance'][0]['marks'][0]['cue_id'];reject('duplicate_cue_ids',lambda:validate_model(duplicate,r))
 unknown=changed(m,('screen_guidance',0,'marks',1,'text_ref'),'invented_note');reject('untrusted_note_reference',lambda:validate_model(unknown,r))
 reject('missing_stop',lambda:validate_model(m,r,'MAX_TOKENS'))
 reject('late_malformed_output',lambda:strict(json.dumps(m)+' trailing output'))
 reject('duplicate_json_fields',lambda:strict('{"criteria":[],"criteria":[]}'))
 reject('nonfinite_geometry',lambda:strict('{"x":NaN}'))
 reject('overflowing_json_number',lambda:strict('{"x":1e309}'))
 old=copy.deepcopy(m);old.pop('screen_guidance');reject('old_three_field_response_not_silently_upgraded',lambda:validate_model(old,r))
 wrong=copy.deepcopy(m);wrong['screen_guidance'][0]['marks'][0]['svg']='<svg/>';reject('raw_svg_forbidden',lambda:validate_model(wrong,r))
 extra=copy.deepcopy(m);extra['screen_guidance'].append(copy.deepcopy(extra['screen_guidance'][0]));reject('duplicate_action_candidate',lambda:validate_model(extra,r))
 cancel=load('cancel.view-change.json');cancel_runtime={**r,'current_context':cancel['context'],'last_cue_sequence':1};accept('view_cancel',lambda:validate_cancel(cancel,cancel_runtime),'clear_only')
 reject('late_packet_after_cancel',lambda:validate_commit(p,{**r,'current_context':cancel['context'],'last_cue_sequence':2},m))
 reject('out_of_order_cancel',lambda:validate_cancel(cancel,{**cancel_runtime,'last_cue_sequence':3}))
 reject('duplicate_cancel_id',lambda:validate_cancel(cancel,{**cancel_runtime,'seen_cancel_ids':[cancel['cancel_id']]}))
 reject('resolved_packet_relabelled_for_advanced_action',lambda:validate_commit(p,load('trusted.action-advance.json'),load('model.action-advance.json')))
 live=copy.deepcopy(p);live['source_binding'].update(surface='live_workspace',transform_revision=1);live['packet']['delivery'].update(surface='live_workspace',adapter_binding_id=live['source_binding']['binding_id'],transform_revision=1);reject('missing_live_adapter_capability',lambda:validate_commit(live,{**r,'source_binding':live['source_binding']},m))
 for name in ('stale-view','stale-visit','stale-condition'):
  reject('fixture_'+name,lambda name=name:validate_commit(load('invalid/'+name+'.json'),r,m))
 reject('fixture_stale_text_only',lambda:validate_commit(load('invalid/stale-text-only.json'),r,load('model.text-only.json')))
 reject('boolean_live_adapter_flag_is_not_proof',lambda:validate_commit(live,{**r,'source_binding':live['source_binding'],'live_binding_verified':True},m))
 trace=load('ordering.trace.json');require(trace['steps'][1]['cue_sequence']>trace['steps'][0]['cue_sequence']>trace['steps'][2]['cue_sequence']-1,'invalid_order_fixture')
 newer=copy.deepcopy(p);newer['cue_sequence']=3;newer['packet']['cue_sequence']=3;reject('newer_sequence_cannot_revive_old_view',lambda:validate_commit(newer,{**r,'current_context':cancel['context'],'last_cue_sequence':2},m))
 manifest={'schema':'analysis-owned-guidance-contract-acceptance/v0.1','proposal_only':True,'runtime_implemented':False,'renderer_interoperability_verified':False,'paint_ack_verified':False,'paid_model_calls':0,'acceptance_count':len(cases),'cases':cases}
 # stdout is a machine-readable report; no source files are generated by checks.
 print(json.dumps(manifest,indent=2));require(len(cases)>=30,'incomplete_acceptance_set')
