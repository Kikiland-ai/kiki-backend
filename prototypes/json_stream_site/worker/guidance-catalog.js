const WRITING_ACTIONS={
 'CP-DSB-01/create':['workspace.canvas'], 'CP-DSB-01/save':['workspace.model_title'],
 'CP-DSB-02/message':['message.block'], 'CP-DSB-02/carrier':['carrier.block'],
 'CP-DSB-03/message-settings':['message.frequency'], 'CP-DSB-03/carrier-settings':['carrier.frequency'],
 'CP-DSB-04/message-wire':['modulator.message_input'],
 'CP-DSB-05/local-settings':['local_carrier.frequency','local_carrier.phase'], 'CP-DSB-05/modulated-wire':['receiver.modulated_input'],
 'CP-DSB-06/filter-settings':['lowpass.numerator','lowpass.denominator'], 'CP-DSB-06/gain-settings':['recovery_gain.value'],
 'CP-DSB-08/stop-time':['simulation.stop_time'], 'CP-DSB-08/solver':['simulation.solver'], 'CP-DSB-08/max-step':['simulation.max_step'],
 'CP-DSB-09/run':['simulation.run_control'],
 'CP-DSB-10/compare':['recovery_scope.original_trace','recovery_scope.recovered_trace'],
 'CP-DSB-11/phase':['local_carrier.phase'], 'CP-DSB-11/run':['simulation.run_control'],
 'CP-DSB-11/inspect':['recovery_scope.original_trace','recovery_scope.recovered_trace'],
 'CP-DSB-12/restore':['local_carrier.phase'], 'CP-DSB-12/rerun':['simulation.run_control'],
 'CP-DSB-12/recovery':['recovery_scope.original_trace','recovery_scope.recovered_trace'], 'CP-DSB-12/save':['model.save_control'],
};
function guidanceActions(s){
 const guide=labProjection(s).guidance,current=guide.current_action;if(!current)return [];
 const rows=GUIDED_POLICY.procedures[s.queue.current_checkpoint_id],at=rows.findIndex(a=>a.id===current.id);
 return rows.slice(at,at+2).map(action=>{
  const ids=WRITING_ACTIONS[action.id]||['workspace.canvas'],targets=ids.map(id=>WRITING_TARGETS.targets.find(t=>t.target_id===id));
  const instruction=action.id===current.id?guide.instruction:action.title,texts={action_title:action.title};
  if(instruction.length<=160)texts.canonical_instruction=instruction;
  for(const [i,v] of targets.map(t=>(action.settings||[]).find(v=>t.parameter_name&&v.field.startsWith(t.parameter_name))).filter(Boolean).slice(0,2).entries())texts['setting_'+i]=v.field+' = '+v.value;
  return {action_id:action.id,checkpoint_id:s.queue.current_checkpoint_id,teaching_intent:targets.every(t=>t.kind==='trace')?'compare_waveforms':targets.every(t=>t.kind==='parameter_field')?'highlight_parameter':'show_action_target',canonical_instruction:instruction,canonical_reason:guide.reason||action.expected_result||'Follow the authored current lab action.',required_target_ids:ids,target_labels:Object.fromEntries(targets.map(t=>[t.target_id,t.semantic_label])),subcriteria:Object.fromEntries(targets.map(t=>[t.target_id,t.criterion_ids.filter(id=>id.startsWith(s.queue.current_checkpoint_id+':'))])),overlay_texts:texts,relationships:targets.every(t=>t.kind==='trace')&&targets.length===2?[{relationship_id:'compare_traces',kind:'compares_with',from_target_id:ids[0],to_target_id:ids[1]}]:[]};
 });
}
