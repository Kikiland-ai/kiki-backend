/* Deterministic contract consumer: no target recognition or teaching decisions. */
(() => {
 const canonical=v=>Array.isArray(v)?'['+v.map(canonical).join(',')+']':v&&typeof v==='object'?'{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')+'}':JSON.stringify(v);
 const same=(a,b)=>canonical(a)===canonical(b),need=(ok,reason)=>{if(!ok)throw Error(reason);};
 function context(state){const cp=state.queue.current_checkpoint_id;return {lab_session_id:state.lab_session_id,experiment_id:state.experiment_id,checkpoint_id:cp,visit_id:state.steps.find(s=>s.checkpoint_id===cp)?.current_visit_id,lab_revision:state.revision,workspace_id:state.workspace.id,capture_epoch:state.workspace.capture_epoch,parameter_revision:state.workspace.parameter_revision,view_revision:state.workspace.view_revision,condition:state.workspace.condition};}
 function validate(e,state){
  need(e?.schema==='analysis-owned-guidance/v0.1'&&e.message_type==='committed_guidance'&&e.model_contract==='lab-observer-drawing/v1'&&e.stream_contract==='lab-analysis-stream/v3','Unsupported drawing contract');
  need(state.status==='active'&&state.runtime.capture_active&&state.observation.status==='available'&&same(e.context,context(state)),'Stale drawing context');
  need(e.action_id===state.guidance.current_action?.id&&e.frame.observation_id===state.observation.observation_id,'Stale drawing action or observation');
  need(e.source_binding.surface==='live_workspace'&&e.source_binding.transform_revision>0,'Unsupported live transform');
  if(e.outcome==='none'){need(e.packet===null,'Invalid no-cue replacement');return;}
  const p=e.packet;need(p?.schema==='screen-writing/v0.2'&&p.message_type==='resolved_packet'&&p.request_id===e.analysis_request_id&&p.guidance_stream_id===e.guidance_stream_id&&p.cue_sequence===e.cue_sequence&&same(p.frame,e.frame)&&same(p.context,e.context)&&same(p.validity,e.validity),'Foreign drawing packet');
  need(p.delivery.surface==='live_workspace'&&p.delivery.adapter_binding_id===e.source_binding.binding_id&&p.delivery.transform_revision===e.source_binding.transform_revision&&p.delivery.pointer_events==='none'&&p.delivery.clip_to_frame&&p.replacement==='replace_complete_guidance_layer','Invalid delivery surface');
  need(p.fallback.instruction===state.guidance.instruction,'Foreign canonical instruction');
  need(e.outcome==='text_only'?p.operations.length===0&&p.fallback.reason==='unresolved_required_target':p.fallback.reason==='none'&&p.resolved_targets.every(t=>t.status==='resolved'),'Invalid unresolved guidance');
  compile(e);
 }
 function compile(e){
  if(!e.packet)return [];const targets=new Map(e.packet.resolved_targets.map(t=>[t.target_id,t]));
  need(targets.size===e.packet.resolved_targets.length,'Duplicate target');
  const region=id=>{const t=targets.get(id),r=t?.region;need(t?.status==='resolved'&&r&&['x','y','width','height'].every(k=>Number.isFinite(r[k])&&r[k]>=0&&r[k]<=1)&&r.width>0&&r.height>0&&r.x+r.width<=1&&r.y+r.height<=1,'Unresolved target');return r;};
  const anchor=a=>{const r=region(a?.target_id);need([a.u,a.v].every(v=>Number.isFinite(v)&&v>=0&&v<=1),'Invalid anchor');return {x:r.x+a.u*r.width,y:r.y+a.v*r.height};};
  need(e.packet.operations.length<=4,'Too many marks');
  return e.packet.operations.map(op=>{need(op.meaning==='lab'&&typeof op.accessible_label==='string','Invalid meaning');const base={kind:op.kind,meaning:op.meaning,label:op.accessible_label};
   if(['box','ellipse'].includes(op.kind))return {...base,region:region(op.target_id)};
   if(op.kind==='text'){need(typeof op.text==='string'&&op.text.length<=160,'Invalid note');return {...base,text:op.text,anchor:anchor(op.anchor)};}
   if(op.kind==='arrow')return {...base,anchors:[anchor(op.from),anchor(op.to)]};throw Error('Unsupported primitive');
  });
 }
 function ack(e,status,reason,binding=null){return {schema:'screen-writing/v0.2',message_type:'delivery_ack',ack_id:crypto.randomUUID(),request_id:e.analysis_request_id||null,packet_id:e.packet?.packet_id||null,cancel_id:e.cancel_id||null,guidance_stream_id:e.guidance_stream_id,cue_sequence:e.cue_sequence,context:e.context,actual_surface:['cancelled','rejected'].includes(status)?'none':status==='text_only'?'guide_panel':'live_workspace',delivered_at:new Date().toISOString(),timestamp_authority:'consumer_clock',status,reason,adapter_binding_id:['cancelled','rejected'].includes(status)?null:binding.sessionId,transform_revision:['cancelled','rejected'].includes(status)?null:binding.revision,packet_context:e.packet?.context||null};}
 globalThis.KikiGuidanceProtocol={validate,compile,ack,context,same};
})();
