// Temporary Worker adapter for the exported Python prototype policy.
// Its model evidence is explicitly unreviewed and never establishes mastery.
function guidedStep(s){return s.steps.find(v=>v.checkpoint_id===s.queue.current_checkpoint_id);}
function guidedClear(s,keepHistory=false){
 if(!keepHistory)s.procedure_history={};
 s.auto_tracking={};s.procedure_tracking={};
 for(const c of guidedStep(s)?.criteria||[])if(c.completion_basis==='screen_inferred')Object.assign(c,{state:'unknown',evidence_ids:[],completion_basis:null});
}
function guidedFinish(s){
 const step=guidedStep(s),cp=checkpoint(s);
 if(!step||s.status!=='active'||!s.runtime.capture_active||!step.criteria.every(c=>c.state==='satisfied')||s.workspace.condition!==GUIDED_POLICY.conditions[cp.id])return false;
 for(const c of step.criteria)if(c.completion_basis==='screen_inferred'){
  const seen=s.auto_tracking?.[c.criterion_id];if(!seen||Date.now()-seen.last_seen_ms>GUIDED_POLICY.support_age_ms)return false;
 }
 labTiming(s);step.status='done';step.completion_basis='screen_inferred_or_student_report';step.assessment_status='unassessed';
 s.queue.done_checkpoint_ids.push(cp.id);s.queue.current_checkpoint_id=s.queue.upcoming_checkpoint_ids.shift()||null;
 const next=guidedStep(s);
 if(next){next.status='in_progress';next.current_visit_id=crypto.randomUUID();next.visits.push(next.current_visit_id);next.attempt_count++;next.timing.entered_at=nowISO();
  const condition=GUIDED_POLICY.conditions[next.checkpoint_id];if(condition!==s.workspace.condition){s.workspace.condition=condition;s.workspace.parameter_revision++;s.workspace.condition_basis='checkpoint_intent_not_verified_model_state';}}
 else s.status='completed';
 if(cp.id==='CP-DSB-01')s.workspace.confirmed=true;
 s.runtime.candidate=null;s.observation.status='awaiting_frame';s.auto_tracking={};s.procedure_tracking={};s.procedure_history={};return true;
}
function guidedObserve(s,candidate){
 if(s.progression_mode!=='screen_guided')return false;
 const step=guidedStep(s),cp=checkpoint(s),now=Date.now(),scope={};
 for(const k of ['visit_id','workspace_id','capture_epoch','parameter_revision','condition'])scope[k]=candidate.admitted_context[k];
 const excluded=new Set([...(GUIDED_POLICY.confirmations[cp.id]||[]),...Object.keys(GUIDED_POLICY.responses)]);
 s.auto_tracking ||= {};
 for(const finding of candidate.criteria){const id=finding.criterion_id;let old=s.auto_tracking[id]||{};
  if(JSON.stringify(old.scope)!==JSON.stringify(scope)||now-(old.last_seen_ms||0)>GUIDED_POLICY.support_age_ms)old={};
  if(finding.status==='mismatch')delete s.auto_tracking[id];
  else if(finding.status==='match'&&old.last_frame_id!==candidate.source_frame.frame_id)s.auto_tracking[id]={scope,count:Math.min(GUIDED_POLICY.minimum_matches,(old.count||0)+1),last_seen_ms:now,last_frame_id:candidate.source_frame.frame_id,frame_ids:[...(old.frame_ids||[]),candidate.source_frame.frame_id].slice(-GUIDED_POLICY.minimum_matches),last_evidence:finding.evidence};
 }
 for(const [id,v]of Object.entries(s.auto_tracking))if(JSON.stringify(v.scope)!==JSON.stringify(scope)||now-v.last_seen_ms>GUIDED_POLICY.support_age_ms)delete s.auto_tracking[id];
 s.procedure_tracking ||= {};
 for(const finding of candidate.action_findings||[]){const id=finding.action_id;let old=s.procedure_tracking[id]||{};
  if(JSON.stringify(old.scope)!==JSON.stringify(scope)||now-(old.last_seen_ms||0)>GUIDED_POLICY.support_age_ms)old={};
  if(finding.status==='mismatch')delete s.procedure_tracking[id];
  else if(finding.status==='match'&&old.last_frame_id!==candidate.source_frame.frame_id)s.procedure_tracking[id]={scope,count:Math.min(GUIDED_POLICY.minimum_matches,(old.count||0)+1),last_seen_ms:now,last_frame_id:candidate.source_frame.frame_id,frame_ids:[...(old.frame_ids||[]),candidate.source_frame.frame_id].slice(-GUIDED_POLICY.minimum_matches),last_evidence:finding.evidence};
 }
 for(const [id,v] of Object.entries(s.procedure_tracking))if(JSON.stringify(v.scope)!==JSON.stringify(scope)||now-v.last_seen_ms>GUIDED_POLICY.support_age_ms)delete s.procedure_tracking[id];
 s.procedure_history ||= {};
 for(const [id,v] of Object.entries(s.procedure_history))if(['visit_id','workspace_id','parameter_revision','condition'].some(k=>v.scope[k]!==scope[k]))delete s.procedure_history[id];
 for(const finding of candidate.action_findings||[]){if(finding.status==='mismatch')delete s.procedure_history[finding.action_id];else if(s.procedure_tracking[finding.action_id]?.count>=GUIDED_POLICY.minimum_matches)s.procedure_history[finding.action_id]=structuredClone(s.procedure_tracking[finding.action_id]);}
 for(const [id,parts] of Object.entries(GUIDED_POLICY.criterion_parts))if(id.startsWith(cp.id+':')){if(!candidate.criteria.some(f=>f.criterion_id===id&&f.status==='mismatch')&&parts.every(a=>s.procedure_tracking[a]?.count>=GUIDED_POLICY.minimum_matches)){
  const reads=parts.map(a=>s.procedure_tracking[a]);s.auto_tracking[id]={scope,count:GUIDED_POLICY.minimum_matches,last_seen_ms:Math.min(...reads.map(r=>r.last_seen_ms)),last_frame_id:candidate.source_frame.frame_id,frame_ids:[...new Set(reads.flatMap(r=>r.frame_ids))],derived_action_ids:parts};
 }else if(s.auto_tracking[id]?.derived_action_ids)delete s.auto_tracking[id];}
 for(const c of step.criteria){const seen=s.auto_tracking[c.criterion_id],ok=!excluded.has(c.criterion_id)&&seen?.count>=GUIDED_POLICY.minimum_matches;
  if(ok&&c.state!=='satisfied'){const evidenceId=crypto.randomUUID();s.evidence.push({id:evidenceId,kind:'screen_observation',origin:'vision_model',review_status:'unreviewed',synthetic:false,checkpoint_id:cp.id,visit_id:step.current_visit_id,workspace_id:s.workspace.id,capture_epoch:s.workspace.capture_epoch,parameter_revision:s.workspace.parameter_revision,frame_ids:seen.frame_ids,observation_id:candidate.observation_id,context:candidate.admitted_context});
   Object.assign(c,{state:'satisfied',completion_basis:'screen_inferred',review_basis:'screen_inferred',evidence_ids:[evidenceId],parameter_revision:s.workspace.parameter_revision});}
  else if(!ok&&c.completion_basis==='screen_inferred')Object.assign(c,{state:'unknown',completion_basis:null,evidence_ids:[],review_basis:null});
 }
 return guidedFinish(s);
}
function guidedProcedure(s){
 const cp=checkpoint(s),satisfied=new Set((guidedStep(s)?.criteria||[]).filter(c=>c.state==='satisfied').map(c=>c.criterion_id));
 const procedure=(GUIDED_POLICY.procedures[cp?.id]||[]).map(item=>{const seen=s.procedure_tracking?.[item.id];
  const byCriterion=(item.satisfied_by.length&&item.satisfied_by.every(id=>satisfied.has(id)))||item.implied_by_any.some(id=>satisfied.has(id));
  const byScreen=item.kind==='visible'&&seen?.count>=GUIDED_POLICY.minimum_matches&&Date.now()-seen.last_seen_ms<=GUIDED_POLICY.support_age_ms;
  const historical=item.kind==='visible'&&s.procedure_history?.[item.id]?.count>=GUIDED_POLICY.minimum_matches;return {...item,tracked:Boolean(byCriterion||byScreen||historical),tracking_basis:byCriterion?'checkpoint_evidence_or_report':byScreen?'recent_screen_support':historical?'historical_screen_support':null};});
 let pending=procedure.filter(a=>!a.tracked);const done=s.queue.done_checkpoint_ids;let current=pending[0]||null;
 if(!current){const checks=[];for(const missing of (guidedStep(s)?.criteria||[]).filter(c=>c.state!=='satisfied').map(c=>c.criterion_id)){
  const parts=GUIDED_POLICY.criterion_parts[missing]||[];
  for(const item of procedure){if(!item.satisfied_by.includes(missing)&&!parts.includes(item.id))continue;const reading=s.procedure_tracking?.[item.id];
   if(parts.length&&reading?.count>=GUIDED_POLICY.minimum_matches&&Date.now()-reading.last_seen_ms<=GUIDED_POLICY.support_age_ms)continue;
   checks.push({...item,verification_only:true,title:item.verify_title,how:item.kind==='visible'?[item.settings.length?'Bring the named block’s settings into view and keep the table fields readable. Only change a value if it differs from the table.':'Bring the named blocks and their existing connections into view, with both endpoints readable.']:item.how});
  }
 }pending=checks;current=pending[0]||null;}

 return {procedure,current_action:current,next_action:pending[1]||null,action_position:current?procedure.findIndex(a=>a.id===current.id)+1:procedure.length,procedure_version:GUIDED_POLICY.procedure_version,tracked_in_stage:procedure.filter(a=>a.tracked).map(a=>({id:a.id,evidence:s.procedure_tracking?.[a.id]?.last_evidence||s.procedure_history?.[a.id]?.last_evidence||null,basis:a.tracking_basis})),
  already_tracked:GUIDED_POLICY.completed_summaries[done.at(-1)]||null,already_tracked_basis:'earlier_checkpoint_record_not_new_screen_claim'};
}
function guidedInstruction(s){return guidedProcedure(s).current_action?.title||'Keep the completed stage visible while I check its remaining evidence.';}
function guidedNext(s){return guidedProcedure(s).next_action?.title||GUIDED_POLICY.procedures[s.queue.upcoming_checkpoint_ids[0]]?.[0].title||null;}
