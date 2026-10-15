// Opt-in producer only. Existing builder/routes intentionally do not import this module.
import {FindingParserJS,streamStrictJSON} from './stream-core.js';
import {MODEL_SCHEMA,GUIDANCE_SCHEMA,DRAWING_SCHEMA} from './guidance-contracts.js';
export const DRAWING_MODEL_CONTRACT='lab-observer-drawing/v1';
export const DRAWING_PROMPT_VERSION='dsb-step-observer/v5-drawing1';
const copy=value=>structuredClone(value),same=(a,b)=>canonical(a)===canonical(b);
function canonical(v){if(Array.isArray(v))return '['+v.map(canonical).join(',')+']';if(v&&typeof v==='object')return '{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')+'}';return JSON.stringify(v);}
function need(ok,reason){if(!ok)throw Error(reason);}
function unique(rows,key){const values=rows.map(r=>r[key]);need(new Set(values).size===values.length,'duplicate_'+key);return values;}
const documents=new Map([MODEL_SCHEMA,GUIDANCE_SCHEMA,DRAWING_SCHEMA].map(s=>[s.$id,s]));
// Deliberately restricted validator for the exact pinned schema vocabulary, not a
// general JSON Schema implementation. Python jsonschema remains independent oracle.
function validate(value,schema,root=schema){
 if(schema.$ref){const [urn,pointer='']=schema.$ref.split('#');const document=urn?documents.get(urn):root;let node=document;need(node,'unknown_schema');for(const key of pointer.slice(1).split('/').filter(Boolean))node=node[key];validate(value,node,document);}
 const pass=s=>{try{validate(value,s,root);return true;}catch{return false;}};
 if(schema.oneOf)need(schema.oneOf.filter(pass).length===1,'schema_oneOf');
 if(schema.allOf)for(const s of schema.allOf)validate(value,s,root);
 if(schema.if)validate(value,pass(schema.if)?schema.then||{}:schema.else||{},root);
 if(Object.hasOwn(schema,'const'))need(same(value,schema.const),'schema_const');
 if(schema.enum)need(schema.enum.some(v=>same(v,value)),'schema_enum');
 const types={null:value===null,object:!!value&&typeof value==='object'&&!Array.isArray(value),array:Array.isArray(value),string:typeof value==='string',number:typeof value==='number'&&Number.isFinite(value),integer:Number.isSafeInteger(value),boolean:typeof value==='boolean'};
 if(schema.type)need((Array.isArray(schema.type)?schema.type:[schema.type]).some(t=>types[t]),'schema_type');
 if(types.object){const keys=Object.keys(value),props=schema.properties||{};for(const k of schema.required||[])need(Object.hasOwn(value,k),'schema_required');
  if(schema.additionalProperties===false)need(keys.every(k=>Object.hasOwn(props,k)),'schema_extra');
  if(schema.minProperties!==undefined)need(keys.length>=schema.minProperties,'schema_minProperties');if(schema.maxProperties!==undefined)need(keys.length<=schema.maxProperties,'schema_maxProperties');
  for(const key of keys){if(schema.propertyNames)validate(key,schema.propertyNames,root);if(props[key])validate(value[key],props[key],root);else if(schema.additionalProperties&&typeof schema.additionalProperties==='object')validate(value[key],schema.additionalProperties,root);}
 }
 if(types.array){if(schema.minItems!==undefined)need(value.length>=schema.minItems,'schema_minItems');if(schema.maxItems!==undefined)need(value.length<=schema.maxItems,'schema_maxItems');if(schema.items)for(const v of value)validate(v,schema.items,root);if(schema.uniqueItems)need(new Set(value.map(canonical)).size===value.length,'schema_uniqueItems');if(schema.contains)need(value.some(v=>{try{validate(v,schema.contains,root);return true;}catch{return false;}}),'schema_contains');}
 if(types.string){const n=[...value].length;if(schema.minLength!==undefined)need(n>=schema.minLength,'schema_minLength');if(schema.maxLength!==undefined)need(n<=schema.maxLength,'schema_maxLength');if(schema.pattern)need(new RegExp(schema.pattern,'u').test(value),'schema_pattern');if(schema.format==='date-time')need(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/.test(value)&&Number.isFinite(Date.parse(value)),'schema_datetime');}
 if(types.number){if(schema.minimum!==undefined)need(value>=schema.minimum,'schema_minimum');if(schema.maximum!==undefined)need(value<=schema.maximum,'schema_maximum');if(schema.exclusiveMinimum!==undefined)need(value>schema.exclusiveMinimum,'schema_exclusiveMinimum');}
 return value;
}
const SOURCE_KEYS=['lab_session_id','experiment_id','workspace_id','capture_epoch','view_revision','parameter_revision','condition'];
export function validateDrawingModel(value,admission,cp,actions){
 validate(value,MODEL_SCHEMA);
 need(same(unique(value.criteria,'criterion_id').sort(),cp.completion_criteria.map(c=>c.id).sort()),'foreign_or_missing_criteria');
 need(same(unique(value.action_findings,'action_id').sort(),actions.map(a=>typeof a==='string'?a:a.id).sort()),'foreign_or_missing_findings');
 need([...value.criteria,...value.action_findings].every(r=>r.evidence.length<=180&&(r.status==='unknown'||r.evidence.trim())),'invalid_evidence');
 unique(value.screen_guidance,'action_id');
 for(const c of value.screen_guidance){const a=admission.eligible_actions.find(a=>a.action_id===c.action_id);need(a,'ineligible_action');unique(c.targets,'target_id');unique(c.marks,'cue_id');if(c.mode==='none')continue;
  need(same(c.targets.map(t=>t.target_id).sort(),[...a.required_target_ids].sort()),'foreign_or_missing_targets');
  for(const t of c.targets)if(t.region)need(t.region.x+t.region.width<=1&&t.region.y+t.region.height<=1,'out_of_frame_region');
  for(const m of c.marks){const refs=['box','ellipse'].includes(m.kind)?[m.target_id]:m.kind==='text'?[m.anchor.target_id]:[m.from.target_id,m.to.target_id];need(refs.every(t=>a.required_target_ids.includes(t)),'unrelated_operation_target');
   if(m.kind==='text')need(Object.hasOwn(a.overlay_texts,m.text_ref),'foreign_text_reference');
   if(m.kind==='arrow'){const r=a.relationships.find(r=>r.relationship_id===m.relationship_id);need(r&&r.from_target_id===m.from.target_id&&r.to_target_id===m.to.target_id,'foreign_relationship');}
  }
 }
 return value;
}
function providerSchema(node){
 if(Array.isArray(node))return node.map(providerSchema);if(!node||typeof node!=='object')return node;
 if(node.$ref){const [urn,pointer]=node.$ref.split('#');let s=documents.get(urn);for(const p of pointer.slice(1).split('/'))s=s[p];return providerSchema(s);}
 const out={},allowed=new Set(['type','required','additionalProperties','items','minItems','maxItems','minimum','maximum','minLength','maxLength','enum']);
 for(const [k,v] of Object.entries(node))if(k==='properties')out[k]=Object.fromEntries(Object.entries(v).map(([n,s])=>[n,providerSchema(s)]));else if(k==='const')out.enum=[v];else if(k==='oneOf')out.anyOf=providerSchema(v);else if(k==='exclusiveMinimum')out.minimum=v;else if(allowed.has(k))out[k]=providerSchema(v);
 return out;
}
export class DrawingFindingParserJS extends FindingParserJS{
 constructor(cp,actions,admission){super(cp,actions,true);this.fields.add('screen_guidance');this.admission=admission;this.cp=cp;this.actions=actions;}
 finish(){return validateDrawingModel(super.finish(),this.admission,this.cp,this.actions);}
}
export class DrawingRunJS{
 constructor(admission){this.admission=copy(admission);this.used=false;this.model=null;}
 async extendRequest(body,bytes,cp,actions,context){
  need(!this.used,'drawing_run_reused');this.used=true;validate(this.admission,GUIDANCE_SCHEMA);const a=this.admission;
  need(a.message_type==='analysis_input'&&same(a.admitted_context,context)&&cp.id===context.checkpoint_id,'foreign_admission_context');
  unique(a.eligible_actions,'action_id');need(a.current_action_id===a.eligible_actions[0].action_id&&a.eligible_actions[0].checkpoint_id===cp.id,'input_action_order');
  for(const action of a.eligible_actions){need(new Set(action.required_target_ids).size===action.required_target_ids.length,'duplicate_required_target');need(same(Object.keys(action.target_labels).sort(),[...action.required_target_ids].sort())&&same(Object.keys(action.subcriteria).sort(),[...action.required_target_ids].sort()),'target_catalogue_mismatch');unique(action.relationships,'relationship_id');need(action.relationships.every(r=>action.required_target_ids.includes(r.from_target_id)&&action.required_target_ids.includes(r.to_target_id)),'foreign_relationship_target');need(action.canonical_instruction.length<=1000&&Object.values(action.overlay_texts).every(t=>t.length<=160),'invalid_authored_text');}
  const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),v=>v.toString(16).padStart(2,'0')).join('');
  need(a.frame.byte_count===bytes.byteLength&&a.frame.sha256===digest&&a.frame.view_revision===context.view_revision,'foreign_frame_pixels');
  need(same(jpegDimensions(bytes),[a.frame.encoded_width,a.frame.encoded_height]),'foreign_frame_dimensions');
  need(utc(a.frame.received_at)<=utc(a.frame.admitted_at)&&utc(a.frame.admitted_at)<utc(a.frame_handle.expires_at),'invalid_admission_clock');
  const schema=providerSchema(MODEL_SCHEMA);
  for(const [key,name,values] of [['criteria','criterion_id',cp.completion_criteria.map(c=>c.id)],['action_findings','action_id',actions.map(a=>a.id)]]){const s=schema.properties[key];s.minItems=s.maxItems=values.length;s.items.properties[name].enum=values;s.items.properties.evidence.maxLength=180;}
  schema.properties.screen_guidance.items.properties.action_id.enum=a.eligible_actions.map(a=>a.action_id);
  const targetIds=[...new Set(a.eligible_actions.flatMap(a=>a.required_target_ids))].sort();
  const scopeTargets=node=>{if(Array.isArray(node))node.forEach(scopeTargets);else if(node&&typeof node==='object'){if(node.properties?.target_id)node.properties.target_id.enum=targetIds;Object.values(node).forEach(scopeTargets);}};scopeTargets(schema.properties.screen_guidance.items);
  body.generationConfig.responseJsonSchema=schema;
  let text=body.systemInstruction.parts[0].text.split('\nSHORT DECISION CONTRACT')[0];const prefix='\nSerialize top-level JSON fields in this order:';if(text.includes(prefix)){const at=text.indexOf(prefix),tail=text.slice(at+prefix.length);text=text.slice(0,at)+'\nOcclusion check'+tail.split('\nOcclusion check')[1];}body.systemInstruction.parts[0].text=text;
  body.systemInstruction.parts[0].text+='\nDRAWING CONTRACT lab-observer-drawing/v1 overrides the earlier three-field close instruction. Return exactly criteria, action_findings, uncertainties, screen_guidance in that order, then finish. Keep every authored finding ID exactly once. screen_guidance has at most two distinct eligible action candidates. Do not choose or complete a lab step. For each offered action, locate ALL its required stable target IDs in this exact image; similar controls in different blocks are different targets. Use normalized encoded-frame rectangles. If any required target is unreadable/ambiguous, use text_only with every target and no marks; if inappropriate, omit the candidate or use none with empty targets/marks. annotate requires every target resolved and 1-4 typed marks. No more than two targets. Box/ellipse reference a target; arrows reference the authored relationship and target-relative endpoints (u,v); text uses an authored text_ref and target-relative anchor. Do not invent instructions, labels, frame metadata, clocks, URLs, HTML, SVG or code. Occluded paths remain unknown. Drawing is a proposal for deterministic rendering, never checkpoint evidence.';
  body.contents[0].parts[0].text+='\nAuthored drawing catalogue: '+JSON.stringify(a.eligible_actions);
 }
 parser(cp,actions){return new DrawingFindingParserJS(cp,actions,this.admission);}
 finish(value){this.model=copy(value);const {screen_guidance,...findings}=value;return findings;}
}
function utc(v){need(typeof v==='string'&&/(Z|\+00:00)$/.test(v)&&Number.isFinite(Date.parse(v)),'server_utc_required');return Date.parse(v);}
function jpegDimensions(bytes){
 need(bytes[0]===255&&bytes[1]===216,'invalid_jpeg');let i=2;
 while(i<bytes.length){need(bytes[i++]===255,'invalid_jpeg');while(bytes[i]===255)i++;const marker=bytes[i++];if(marker===217||marker===218)break;if(marker===216||marker===1||(marker>=208&&marker<=215))continue;const n=(bytes[i]<<8)|bytes[i+1];need(n>=2&&i+n<=bytes.length,'invalid_jpeg');if([192,193,194,195,197,198,199,201,202,203,205,206,207].includes(marker)){need(n>=8,'invalid_jpeg');return [(bytes[i+5]<<8)|bytes[i+6],(bytes[i+3]<<8)|bytes[i+4]];}i+=n;
 }throw Error('invalid_jpeg');
}
export function buildCommittedDrawing(admission,model,r){
 need(r.session_status==='active'&&r.observation_status==='available','inactive_context');const context=r.current_context;
 validateDrawingModel(model,admission,{completion_criteria:r.expected_criterion_ids.map(id=>({id}))},r.expected_action_ids);
 need(context.lab_revision>admission.admitted_context.lab_revision,'uncommitted_revision');if(context.checkpoint_id===admission.admitted_context.checkpoint_id)need(context.visit_id===admission.admitted_context.visit_id,'stale_visit');
 need(same(r.admitted_context,admission.admitted_context)&&SOURCE_KEYS.every(k=>same(context[k],admission.admitted_context[k])),'stale_source_context');
 need(r.analysis_request_id===admission.analysis_request_id&&['frame','frame_handle','source_binding'].every(k=>same(r[k],admission[k])),'foreign_frame_provenance');
 need(Number.isSafeInteger(r.cue_sequence)&&r.cue_sequence>r.last_cue_sequence,'older_or_cancelled_sequence');
 const a=admission.eligible_actions.find(a=>a.action_id===r.current_action_id);need(a&&a.checkpoint_id===context.checkpoint_id,'unoffered_current_action');need(r.canonical_instruction===a.canonical_instruction,'changed_canonical_instruction');
 const created=utc(r.now),received=utc(admission.frame.received_at);need(received<=utc(admission.frame.admitted_at)&&utc(admission.frame.admitted_at)<=created,'invalid_commit_clock');
 const expires=Math.min(created+8000,received+20000,utc(admission.frame_handle.expires_at));need(created<expires,'expired_frame');
 const c=model.screen_guidance.find(c=>c.action_id===a.action_id),mode=c?.mode||'none',reason=mode==='none'?(c?'model_declined':'no_matching_candidate'):mode==='text_only'?'unresolved_required_target':'none';
 const value={schema:'analysis-owned-guidance/v0.1',message_type:'committed_guidance',model_contract:DRAWING_MODEL_CONTRACT,stream_contract:'lab-analysis-stream/v3',projection_contract:'committed-decision/v2',analysis_request_id:admission.analysis_request_id,guidance_stream_id:r.guidance_stream_id,cue_sequence:r.cue_sequence,context:copy(context),admitted_context:copy(admission.admitted_context),action_id:a.action_id,frame:copy(admission.frame),frame_handle:copy(admission.frame_handle),source_binding:copy(admission.source_binding),replacement:'replace_complete_guidance_layer',validity:{created_at:new Date(created).toISOString(),expires_at:new Date(expires).toISOString(),max_frame_age_ms:20000},outcome:mode,reason,teaching_intent:a.teaching_intent,target_criteria:[],text_bindings:[],packet:null};
 if(mode!=='none'){const binding=admission.source_binding,live=binding.surface==='live_workspace';if(live){const p=r.trusted_live_bindings?.[binding.binding_id];need(Number.isSafeInteger(binding.transform_revision)&&binding.transform_revision>0&&typeof r.owner_id==='string'&&r.owner_id&&p&&p.owner_id===r.owner_id&&p.binding_revision===binding.binding_revision&&p.transform_revision===binding.transform_revision&&same(p.verified_frame,admission.frame)&&p.proof_kind==='native_capture_handle_and_pixel_match','unverified_live_binding');}
  const operations=c.marks.map(m=>{let label;if(m.kind==='arrow'){const rel=a.relationships.find(r=>r.relationship_id===m.relationship_id);label={compares_with:'Compare the indicated targets.',connects_to:'Connect the indicated targets.',influences:'Show the indicated relationship.'}[rel.kind];}else label=a.target_labels[['box','ellipse'].includes(m.kind)?m.target_id:m.anchor.target_id];const op={...copy(m),meaning:'lab',accessible_label:label};if(m.kind==='text'){delete op.text_ref;op.text=a.overlay_texts[m.text_ref];value.text_bindings.push({cue_id:m.cue_id,text_ref:m.text_ref});}return op;});
  value.target_criteria=a.required_target_ids.map(t=>({target_id:t,criterion_ids:a.subcriteria[t]}));const packetId=r.packet_id||crypto.randomUUID();need(!r.seen_packet_ids?.includes(packetId),'duplicate_packet_id');
  value.packet={schema:'screen-writing/v0.2',message_type:'resolved_packet',packet_id:packetId,request_id:admission.analysis_request_id,guidance_stream_id:r.guidance_stream_id,cue_sequence:r.cue_sequence,context:copy(context),frame:copy(admission.frame),resolved_targets:c.targets.map(t=>({...copy(t),method:'model_vision',reason:t.status==='resolved'?'Located in the admitted analysis frame.':'Required target is not established in the admitted frame.'})),relationships:copy(a.relationships),operations,replacement:value.replacement,delivery:{surface:binding.surface,coordinate_space:'normalized_encoded_frame',adapter_binding_id:live?binding.binding_id:null,transform_revision:live?binding.transform_revision:null,pointer_events:'none',clip_to_frame:true},validity:copy(value.validity),fallback:{instruction:a.canonical_instruction,reason}};
 }
 validate(value,GUIDANCE_SCHEMA);need(new TextEncoder().encode(JSON.stringify(value)).length<=32768,'oversized_payload');return value;
}
export {validate as validateGuidanceSchema,streamStrictJSON};

const TRACE_METRICS=new Set(['provider_ms','first_byte_ms','first_finding_ms','critical_fields_ms','provider_stop_ms','drawing_fields_ms','decision_validated_ms','validation_ms','request_prepared_ms','drawing_tail_ms','commit_finished_ms','packet_prepared_ms','publication_ms','frame_age_at_commit_ms','input_tokens','output_tokens','cached_tokens','thinking_tokens','total_tokens','request_text_characters','image_bytes','provider_attempts','stream_attempts','context_db_reads','context_db_ms','routing_db_reads','routing_db_ms','provider_db_operations','provider_db_ms','provider_http_attempts','provider_http_ms','provider_headers_ms','provider_first_dispatch_ms','provider_last_dispatch_ms','screen_guidance_bytes','provider_chunks','context_batches','context_events']);
const TRACE_REASONS=new Set(['none','stale_context','stale_source_context','expired_frame','inactive_context','foreign_frame_provenance','invalid_output','incomplete_output','provider_timeout_or_network_error','analysis_cancelled','unverified_live_binding','no_matching_candidate','unresolved_required_target','model_declined','revision_conflict','cancelled_context','duplicate_publication','stale_stream_context','provider_failure','cancelled']);
export class GuidanceTraceJS{
 constructor(write,{request_id,pair_id,arm,sample_kind,model,configuration_id='unspecified',source_revision='uncommitted',run_id='unspecified'}){need(['control','drawing_v1'].includes(arm)&&['offline_replay','live_provider'].includes(sample_kind),'invalid_comparison_configuration');this.sequence=0;this.write=write;this.started=performance.now();this.tags={schema:'guidance-producer-timing/v1',request_id,pair_id,experiment:'analysis-owned-guidance',arm,sample_kind,model,paint_verified:false,run_id,runtime:'worker',configuration_id,source_revision};}
 emit(stage,metrics={},reason='none'){need(['admitted','analysis_validated','tracker_committed','packet_prepared','published','discarded','failed','cancelled'].includes(stage),'invalid_trace_stage');const safe=Object.fromEntries(Object.entries(metrics).filter(([k,v])=>TRACE_METRICS.has(k)&&(v===null||typeof v==='number'&&Number.isFinite(v)&&v>=0)));const record={...this.tags,event_sequence:++this.sequence,stage,reason:TRACE_REASONS.has(reason)||/^provider_http_[1-5][0-9]{2}$/.test(reason)?reason:'provider_failure',server_time:new Date().toISOString(),elapsed_ms:Math.round((performance.now()-this.started)*1000)/1000,...safe};this.write(record);return record;}
}
// Integration supplies the existing analyzer function; this file does not alter
// shared build/routes or claim the resulting packet was delivered or painted.
export async function runDrawingAnalysis(analyze,bytes,cp,state,env,emit,admission,trace=null){
 const run=new DrawingRunJS(admission);
 try{trace?.emit('admitted',{image_bytes:bytes.byteLength});const output=await analyze(bytes,cp,state,env,emit,run);trace?.emit('analysis_validated',output.timing);return {output,run};}
 catch(error){run.model=null;trace?.emit(error.message==='analysis_cancelled'?'cancelled':error.message==='stale_context'?'discarded':'failed',{},error.message);throw error;}
}
