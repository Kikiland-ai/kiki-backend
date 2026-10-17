import {verificationCadence,sameScreenContent} from '/static/lab-cadence.js';
import {startAnalysisStream} from '/static/json-stream-client.js';
/* Shared browser transport/display. Progress decisions come from the backend. */
(() => {
 const $=id=>document.getElementById(id);
 let state=null,definition=null,policy=null,python=false,latest=null,captureId=null,attaching=null,busy=false,editing=false,viewChanging=false,generation=0;
 let streamEnabled=true,streamRows=[],activeStream=null,acceptedObservation=null,lastFingerprint=null,lastSamplingContext=null,lastBound=false,presentationWake=null;
 const pendingStreams=new Set();
 const clearStream=()=>{streamRows=[];$('lab-stream-feedback').hidden=true;};
 function invalidateStream(){generation++;if(presentationWake!==null){clearTimeout(presentationWake);presentationWake=null;}void window.KikiWriting?.invalidate('Lab context or attachment changed');for(const item of pendingStreams)item.controller.abort();activeStream=null;clearStream();}
 async function streamedCheck(id,selected,version){
  clearStream();const item={controller:new AbortController(),committed:false,first:null,core:null,tail:null};activeStream=item;
  // Only auxiliary delivery is cancelled here; its durable decision is final.
  for(const old of pendingStreams)if(old.committed)old.controller.abort();
  pendingStreams.add(item);const started=performance.now();
  const showTiming=()=>{if(activeStream===item&&version===generation)$('lab-stream-timing').textContent=`This check: first feedback ${item.first===null?'—':(item.first/1000).toFixed(2)+' s'}; committed guidance ${item.core===null?'—':(item.core/1000).toFixed(2)+' s'}; auxiliary ${item.tail===null?'pending':(item.tail/1000).toFixed(2)+' s'}. Verification resumes from the committed decision.`;};
  const context={lab_session_id:id,checkpoint_id:state.queue.current_checkpoint_id,visit_id:python?state.current_visit_id:step().current_visit_id,workspace_id:state.workspace.id,capture_epoch:state.workspace.capture_epoch,view_revision:state.workspace.view_revision,parameter_revision:state.workspace.parameter_revision,condition:state.workspace.condition};
  const drawingHeaders=window.KikiWriting?.requestHeaders(selected)||{};
  const request=python?{headers:{'Content-Type':'application/json'},body:JSON.stringify({revision:state.revision,frame_id:selected.frame.frame_id,view_revision:selected.frame.view_revision})}:{headers:{'Content-Type':'image/jpeg','X-Capture-Frame':JSON.stringify(selected.meta),...drawingHeaders},body:selected.blob};
  let r;try{r=await fetch(`/lab-sessions/${id}/check-stream`,{method:'POST',credentials:'same-origin',...request,signal:AbortSignal.any([item.controller.signal,AbortSignal.timeout(25000)])});}catch(error){pendingStreams.delete(item);throw error;}
  const pipe=startAnalysisStream(r,{expectedFrame:selected.frame,expectedContext:context,streamContract:drawingHeaders['X-Guidance-Contract']?'lab-analysis-stream/v3':null,signal:item.controller.signal,onEvent:event=>{
   if(version!==generation||state?.lab_session_id!==id||activeStream!==item)return;
   if(event.type==='attempt_reset'){item.first=item.core=null;streamRows=[];$('lab-stream-findings').replaceChildren();$('lab-stream-progress').textContent='Trying another available connection…';}
   if(event.type==='admitted'){$('lab-stream-feedback').hidden=false;$('lab-stream-label').textContent='READING THIS FRAME';$('lab-stream-progress').textContent='Checking the visible settings and connections…';}
   if(event.type==='provisional_findings'){if(item.first===null)item.first=performance.now()-started;streamRows.push(event.finding);
    $('lab-stream-findings').replaceChildren(...streamRows.filter(v=>v.evidence).slice(-3).map(v=>{const li=document.createElement('li');li.textContent=`${v.status==='match'?'Visible':v.status==='mismatch'?'Check this':'Not established'}: ${v.evidence}`;return li;}));
    $('lab-stream-label').textContent='TENTATIVE SCREEN CHECK';$('lab-stream-progress').textContent='Finishing verification before tracking progress…';}
   if(event.type==='critical_fields_ready')$('lab-stream-progress').textContent='Settings and action checks received. Finishing verification…';
   if(event.type==='guidance_committed'){item.core=performance.now()-started;}
   // v2 snapshots are an auxiliary historical projection, never a state update.
  }});
  void pipe.completion.then(()=>{item.tail=performance.now()-started;showTiming();}).catch(()=>{if(item.committed&&activeStream===item&&version===generation)$('lab-stream-timing').textContent+=' Auxiliary delivery interrupted; the committed decision is retained.';}).finally(()=>pendingStreams.delete(item));
  const result=await pipe.committed;if(version!==generation||activeStream!==item||state?.lab_session_id!==id)throw new DOMException('Obsolete analysis completion','AbortError');item.committed=true;if(item.core===null)item.core=performance.now()-started;showTiming();return result;
 }
 let nextRetryAt=0,lastCheck=0,lastHash=null,lastCheckpoint=null,lastHeartbeat=0,lastCheckFrameId=null;
 const storage=()=>python?'kiki-python-lab-id':'kiki-last-lab-id';
 function retryDeadline(data){if(data?.runtime?.analysis_status==='waiting_for_provider')nextRetryAt=Date.now()+Math.max(0,data.runtime.retry_after_ms||0);else if(data?.runtime)nextRetryAt=0;}
 const message=text=>{$('lab-status').textContent=text;};
 async function api(path,method='GET',body=null){
  const response=await fetch(path,{method,credentials:'same-origin',signal:AbortSignal.timeout(25000),...(body===null?{}:{headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})});
  const data=await response.json();if(!response.ok)throw Error(typeof data.detail==='string'?data.detail:'The guide could not update.');retryDeadline(data);return data;
 }
 const current=()=>definition?.checkpoints.find(c=>c.id===state?.queue.current_checkpoint_id);
 const step=()=>Array.isArray(state?.steps)?state.steps.find(s=>s.checkpoint_id===state.queue.current_checkpoint_id):state?.steps[state.queue.current_checkpoint_id];
 function confirmationIds(){
  const cp=current()?.id,pending=step()?.criteria.filter(c=>c.state!=='satisfied')||[];
  const primary=(policy.confirmations[cp]||[]).filter(id=>pending.some(c=>c.criterion_id===id));
  return primary.length?primary:(policy.fallback_confirmations[cp]||[]).filter(id=>pending.some(c=>c.criterion_id===id)&&state.runtime.candidate?.criteria.some(c=>c.criterion_id===id&&c.status==='unknown'));
 }
 function render(){
  if(!state||!definition||!policy)return;window.KikiWriting?.context(state);
  $('lab-start').hidden=true;$('lab-run').hidden=false;
  const cp=current(),currentStep=step(),candidate=state.runtime.candidate,guide=state.guidance||{},action=guide.current_action;
  $('lab-model').textContent=python?state.workspace.model_name:state.workspace.external_project_ref;
  $('lab-progress').textContent=`Stage ${cp?.order||12} of 12${action?` · Action ${guide.action_position} of ${guide.procedure.length}`:""} · ${state.queue.done_checkpoint_ids.length} stages tracked`;
  $('lab-current').textContent=state.guidance?.instruction||policy.actions[cp?.id]||'Experiment complete. Download your journal.';
  $('lab-why').textContent=policy.stage_explanations?.[cp?.id]||cp?.why.en||'You can review or export the experiment journal below.';
  const done=guide.already_tracked;
  $('lab-done').hidden=!done;$('lab-done').textContent=done?`Tracked earlier: ${done}`:'';
  const supported=(guide.tracked_in_stage||[]).filter(a=>a.evidence).slice(-2);$('lab-action-history').hidden=!supported.length;$('lab-action-history').textContent=supported.length?`Earlier readings in this stage: ${supported.map(a=>a.evidence).join(' ')}`:'';
  $('lab-action-details').hidden=!action;
  $('lab-where').textContent=action?.where||'';
  $('lab-how').replaceChildren(...(action?.how||[]).map(text=>{const li=document.createElement('li');li.textContent=text;return li;}));
  $('lab-result').textContent=action?.expected_result||'';
  $('lab-settings').hidden=!action?.settings?.length;
  $('lab-settings').querySelector('tbody').replaceChildren(...(action?.settings||[]).map(setting=>{const tr=document.createElement('tr'),field=document.createElement('td'),value=document.createElement('td'),code=document.createElement('code');field.textContent=setting.field;code.textContent=setting.value;value.append(code);tr.append(field,value);return tr;}));
  $('lab-already-help').hidden=!action?.already_done_help;$('lab-already-copy').textContent=action?.already_done_help||'';
  $('lab-stage-plan').hidden=!guide.procedure?.length;
  $('lab-procedure').replaceChildren(...(guide.procedure||[]).map(item=>{const li=document.createElement('li');li.textContent=`${item.title}${item.tracked?' (tracked)':''}`;if(item.id===action?.id)li.setAttribute('aria-current','step');return li;}));
  const next=definition.checkpoints.find(c=>c.id===state.queue.upcoming_checkpoint_ids[0]);
  const nextText=state.guidance?.next_instruction||(next?policy.actions[next.id]:null);
  $('lab-next').textContent=nextText?`Coming next: ${nextText}`:'Coming next: save and review your experiment.';
  $('lab-budget').textContent=`${state.runtime.analysis_attempts} screen reads. Progress is screen-inferred or reported; understanding remains unassessed.`;
  if(candidate&&state.runtime.analysis_status==='available'&&acceptedObservation?.observation_id!==candidate.observation_id)acceptedObservation={...candidate,lab_session_id:state.lab_session_id,context:[state.workspace.id,state.workspace.capture_epoch,state.workspace.view_revision,state.workspace.parameter_revision,state.workspace.condition]};
  const accepted=acceptedObservation?.lab_session_id===state.lab_session_id?acceptedObservation:null,acceptedAge=accepted?Date.now()-(accepted.source_frame.server_received_unix_ms??accepted.source_frame.server_received_unix*1000):Infinity,historical=!accepted||acceptedAge>=20000||JSON.stringify(accepted.context)!==JSON.stringify([state.workspace.id,state.workspace.capture_epoch,state.workspace.view_revision,state.workspace.parameter_revision,state.workspace.condition])||!state.runtime.capture_active;
  const age=candidate?Date.now()-(candidate.source_frame.server_received_unix_ms??candidate.source_frame.server_received_unix*1000):Infinity;
  $('lab-observation').textContent=accepted?`${historical?'Earlier accepted view':'What I can see'}: ${accepted.summary}`:state.status==='completed'?'This experiment’s steps have been tracked.':!latest?'Share the matching model so I can follow along.':'Reading your shared screen. The accepted observation will appear here when verification completes.';
  $('lab-watch-state').textContent=busy?'READING YOUR SCREEN':state.status==='paused'?'GUIDANCE PAUSED':nextRetryAt>Date.now()?`ANALYSIS RETRY IN ${Math.ceil((nextRetryAt-Date.now())/1000)}s`:latest?'FOLLOWING ALONG':'WAITING FOR YOUR SCREEN';
  $('lab-checked').hidden=!candidate;
  if(candidate){const src=`/lab-sessions/${state.lab_session_id}/image?observation=${candidate.observation_id}`;if($('lab-checked').getAttribute('src')!==src)$('lab-checked').src=src;}else $('lab-checked').removeAttribute('src');
  const pending=currentStep?.criteria.filter(c=>c.state!=='satisfied')||[];
  const confirmation=confirmationIds(),primary=confirmation.some(id=>policy.confirmations[cp?.id]?.includes(id));
  $('lab-confirmation').hidden=!confirmation.length||state.status!=='active'||(action&&action.kind!=='confirmation'&&action.kind!=='run');
  $('lab-confirmation-copy').textContent='This needs your confirmation because the screenshot can’t reliably prove it.';
  $('lab-confirm').textContent=primary?policy.confirmation_copy[cp?.id]:policy.fallback_confirmation_copy;$('lab-confirm').disabled=busy||editing||!latest;
  const needsResponse=pending.some(c=>policy.responses[c.criterion_id]);
  $('lab-response').hidden=!needsResponse||(action&&action.kind!=='response');
  $('lab-response-label').textContent=policy.response_copy[cp?.id]||'What did you notice?';
  $('lab-save-answer').disabled=busy||editing;
  $('lab-check').disabled=busy||editing||!latest||state.status!=='active'||!cp;
  $('lab-pause').textContent=state.status==='paused'?'Resume guidance':'Pause guidance';
  $('lab-criteria').replaceChildren(...(cp?.completion_criteria||[]).map(c=>{const row=document.createElement('li'),stored=currentStep.criteria.find(v=>v.criterion_id===c.id);row.textContent=`${stored.state==='satisfied'?'Tracked':'Waiting'}: ${c.description}`;return row;}));
  $('lab-ledger').replaceChildren(...definition.checkpoints.map(c=>{const option=document.createElement('option');option.value=c.id;option.textContent=`${c.order}. ${c.instruction.en}`;option.selected=c.id===cp?.id;return option;}));
  $('lab-history-link').href=`/lab-sessions/${state.lab_session_id}/events`;
 }
 async function refresh(){if(!state)return;const id=state.lab_session_id,version=generation,data=await api(`/lab-sessions/${id}`);if(version===generation&&state?.lab_session_id===id&&data.revision>=state.revision){state=data;render();}}
 async function action(name,extra={}){
  invalidateStream();
  await refresh();const id=state.lab_session_id;
  const path=python?'context':'action',data=await api(`/lab-sessions/${id}/${path}`,'POST',{revision:state.revision,action:name,...extra});
  if(state?.lab_session_id===id){state=data;render();}return data;
 }
 async function attach(id){
  if(!state)return;await refresh();
  if(!python||state.workspace.capture_session_id!==id)state=await api(`/lab-sessions/${state.lab_session_id}/attach`,'POST',{revision:state.revision,capture_session_id:id});
  const generic=$('enable-analysis');if(generic){generic.checked=false;generic.dispatchEvent(new Event('change'));}
  window.KikiWriting?.attach(state,id);render();message('I’m following your model. Keep working in Simulink; the next action will update as I can read it.');
 }
 async function check(force=false){
  if(!state||!latest||busy||editing||viewChanging||state.status!=='active'||!current())return;
  if(Date.now()<nextRetryAt)return;
  const visibleDelay=window.KikiWriting?.nextCheckDelay||0;
  if(!force&&visibleDelay>0){if(presentationWake!==null)clearTimeout(presentationWake);const version=generation,id=state.lab_session_id;presentationWake=setTimeout(()=>{presentationWake=null;if(version===generation&&state?.lab_session_id===id)void check();},Math.ceil(visibleDelay)+1);return;}
  const cp=state.queue.current_checkpoint_id,sampling=JSON.stringify([state.workspace.id,state.workspace.capture_epoch,state.workspace.view_revision,state.workspace.parameter_revision,state.workspace.condition,step().current_visit_id,state.guidance.current_action?.id]),same=cp===lastCheckpoint&&sampling===lastSamplingContext&&!!latest.writingBinding===lastBound&&sameScreenContent({hash:latest.frame?.sha256,fingerprint:latest.visualFingerprint},{hash:lastHash,fingerprint:lastFingerprint});
  const waitingForActionRead=state.runtime.candidate?.action_findings?.some(a=>a.status==='match'&&(state.procedure_tracking?.[a.action_id]?.count||0)<policy.minimum_matches);
  const waitingForSecondRead=state.runtime.candidate?.criteria.some(c=>c.status==='match'&&!policy.confirmations[cp]?.includes(c.criterion_id)&&!policy.responses[c.criterion_id]&&step().criteria.find(v=>v.criterion_id===c.criterion_id)?.state!=='satisfied');
  const evidenceExpiring=Object.values({...state.auto_tracking,...state.procedure_tracking}).some(v=>v.count>=policy.minimum_matches&&Date.now()-v.last_seen_ms>policy.support_age_ms/2);
  const interval=verificationCadence({sameFrame:same,pendingSecondRead:waitingForSecondRead||waitingForActionRead,evidenceExpiring,status:state.runtime.analysis_status},policy);
  if(!force&&(interval===null||Date.now()-lastCheck<interval))return;
  busy=true;lastCheck=Date.now();const version=generation,id=state.lab_session_id;render();
  try{
   if(attaching)await attaching;
   if(python)await refresh();if(version!==generation||!latest)return;
   const selected=latest;lastHash=selected.frame?.sha256;lastCheckpoint=state.queue.current_checkpoint_id;lastCheckFrameId=selected.frame?.frame_id;lastFingerprint=selected.visualFingerprint;lastSamplingContext=sampling;lastBound=!!selected.writingBinding;
   let data;const checkStarted=performance.now();
   if(streamEnabled)data=await streamedCheck(id,selected,version);
   else if(python)data=await api(`/lab-sessions/${id}/check`,'POST',{revision:state.revision,frame_id:selected.frame.frame_id,view_revision:selected.frame.view_revision});
   else {const r=await fetch(`/lab-sessions/${id}/check`,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'image/jpeg','X-Capture-Frame':JSON.stringify(selected.meta),...drawingHeaders},body:selected.blob,signal:AbortSignal.timeout(25000)});data=await r.json();if(!r.ok)throw Object.assign(Error(data.detail||'The guide could not read this frame.'),{status:r.status,retry_after_ms:data.retry_after_ms});}
   if(version!==generation||state?.lab_session_id!==id)return;
   if(!streamEnabled)$('lab-stream-timing').textContent=`Baseline JSON: full response ${((performance.now()-checkStarted)/1000).toFixed(2)} s; feedback arrives at completion.`;
   if(data.revision<state.revision)return;state=data;retryDeadline(data);render();await window.KikiWriting?.receive(state);if(version!==generation)return;if(state.runtime.analysis_status==='waiting_for_provider')lastHash=null;
   message(state.runtime.analysis_status==='waiting_for_provider'?'Analysis is waiting for the provider. Keep working; sharing and progress continue, and I’ll retry automatically.':state.runtime.analysis_status==='failed'?'I couldn’t read that frame. Keep sharing; I’ll try a later view.':state.queue.current_checkpoint_id!==lastCheckpoint?'That step is tracked. Here’s what to do next.':'I’m following along. Steps advance when there is enough visible evidence.');
  }catch(e){lastHash=null;nextRetryAt=Date.now()+(e.retry_after_ms|| (e.status===409?0:policy.fast_interval_ms||3000));if(version===generation){message(e.message);await refresh().catch(()=>{});}}
  finally{clearStream();busy=false;render();
   // A newer received frame can already be waiting. Do not wait for another
   // capture tick or reuse the same source frame as the second observation.
   if(version===generation&&latest?.frame?.frame_id!==undefined&&latest.frame.frame_id!==lastCheckFrameId)setTimeout(()=>{if(version===generation&&state?.lab_session_id===id)void check();},Math.max(0,(policy.fast_interval_ms||3000)-(Date.now()-lastCheck)));
  }
 }
 window.KikiLab={
  viewRevision(){return state?.workspace.view_revision||1;},
  async onViewChange(revision){if(!state||viewChanging)return;viewChanging=true;try{await refresh();if(revision>state.workspace.view_revision)await action('view_changed',{view_revision:revision});}finally{viewChanging=false;}},
  onCaptureStart(id){captureId=id;attaching=attach(id).catch(e=>message(e.message)).finally(()=>{attaching=null;});},
  onFrame(blob,meta,frame,writingBinding=null,visualFingerprint=null){
   latest=python?{frame:blob}:{blob,meta,frame,writingBinding,visualFingerprint};
   if(state){render();if(!python&&Date.now()-lastHeartbeat>10000){lastHeartbeat=Date.now();void (async()=>{if(attaching)await attaching;await api(`/lab-sessions/${state.lab_session_id}/heartbeat`,'POST',{});})().catch(e=>message(e.message));}void check();}
  },
  onCapturePause(paused,id){if(paused)void this.onCaptureStop();else this.onCaptureStart(id);},
  async onCaptureState(){latest=null;invalidateStream();await refresh().catch(e=>message(e.message));},
  async onCaptureStop(){latest=null;invalidateStream();if(!state)return;try{await refresh();if(!python)state=await api(`/lab-sessions/${state.lab_session_id}/detach`,'POST',{revision:state.revision});render();message('Sharing stopped. Your place in the experiment is saved.');}catch(e){message(e.message);}}
 };
 function handler(id,fn){$(id).addEventListener('click',async()=>{try{await fn();}catch(e){message(e.message);}});}
 handler('lab-begin',async()=>{
  const body={operator_trial:true,model_name:$('lab-model-name').value,progression_mode:'screen_guided'};
  state=await api('/lab-sessions','POST',body);localStorage.setItem(storage(),state.lab_session_id);lastCheck=0;lastHash=null;generation++;render();
  if(captureId)await attach(captureId);message('Share your Simulink tab. I’ll read it and guide the next action.');
 });
 $('lab-stream-mode').addEventListener('change',()=>{invalidateStream();streamEnabled=$('lab-stream-mode').value==='stream';lastHash=null;lastCheck=0;message('Analysis mode changed. The next fresh frame will use this mode.');});
 handler('lab-check',()=>check(true));
 handler('lab-confirm',async()=>{
  if(busy||editing)return;
  // This button is an explicit student report, never an automated model review.
  const before=current().id,candidate=state.runtime.candidate,age=candidate?Date.now()-(candidate.source_frame.server_received_unix_ms??candidate.source_frame.server_received_unix*1000):Infinity;
  if(age>18000)await check(true);if(!state||current()?.id!==before)return;
  editing=true;render();
  try{await refresh();const ids=confirmationIds(),primary=ids.some(id=>policy.confirmations[before]?.includes(id));
   const review_note=`Student explicitly confirmed: ${primary?policy.confirmation_copy[before]:policy.fallback_confirmation_copy}. This is a student report, not independent tool verification.`;
   if(python)state=await api(`/lab-sessions/${state.lab_session_id}/review`,'POST',{revision:state.revision,criterion_ids:ids,review_note});
   else state=await api(`/lab-sessions/${state.lab_session_id}/action`,'POST',{revision:state.revision,action:'review',criterion_ids:ids,review_note});
   message('Your confirmation is saved. I’ll continue following the next action.');
  }finally{editing=false;render();}
 });
 handler('lab-save-answer',async()=>{
  if(busy||editing)return;const text=$('lab-answer').value;if(!text.trim())throw Error('Add a short response first.');editing=true;render();
  try{await refresh();if(python)state=await api(`/lab-sessions/${state.lab_session_id}/responses`,'POST',{revision:state.revision,kind:current().id==='CP-DSB-12'?'explanation':'observation',text,self_confidence:null});
   else state=await api(`/lab-sessions/${state.lab_session_id}/action`,'POST',{revision:state.revision,action:'answer',text});
   $('lab-answer').value='';message('Response saved. I’m keeping your explanation separate from what the screen shows.');
  }finally{editing=false;render();}
 });
 handler('lab-pause',async()=>{generation++;await action(state.status==='paused'?'resume':'pause');});
 handler('lab-correction',async()=>{generation++;await action('revisit',{checkpoint_id:state.queue.current_checkpoint_id});lastCheck=0;message('I’ve reset this step’s observations. Show me the relevant part of your model again.');});
 handler('lab-view-changed',()=>window.KikiLab.onViewChange((state?.workspace.view_revision||1)+1));
 handler('lab-parameters',()=>action('parameters_changed'));
 handler('lab-revisit',async()=>{generation++;await action('revisit',{checkpoint_id:$('lab-ledger').value});lastCheck=0;});
 handler('lab-export',async()=>{await refresh();const through=state.revision,events=[];let after=0;while(true){const page=await api(`/lab-sessions/${state.lab_session_id}/events?after=${after}&limit=100`);events.push(...page.filter(e=>e.event_sequence<=through));if(page.length<100||page.at(-1).event_sequence>=through)break;after=page.at(-1).event_sequence;}const url=URL.createObjectURL(new Blob([JSON.stringify({definition,state,events},null,2)],{type:'application/json'}));const link=document.createElement('a');link.href=url;link.download='dsb-sc-lab-journal.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
 handler('lab-delete',async()=>{generation++;await api(`/lab-sessions/${state.lab_session_id}`,'DELETE');state=null;localStorage.removeItem(storage());$('lab-run').hidden=true;$('lab-start').hidden=false;message('This run was deleted.');});
 window.addEventListener('pagehide',()=>{if(state&&!python)navigator.sendBeacon(`/lab-sessions/${state.lab_session_id}/detach`,JSON.stringify({revision:state.revision}));});
 void (async()=>{try{
  python=(await api('/health')).backend==='python_fastapi';
  [definition,policy]=await Promise.all([api('/lab-definition'),api('/lab-guidance-policy')]);
  const id=localStorage.getItem(storage());if(id){state=await api(`/lab-sessions/${id}`);if(state.status!=='completed'&&state.progression_mode!=='screen_guided')await action('enable_guided');render();message('Your place is saved. Share the same model to continue.');}
 }catch(e){message(e.message);}})();
})();
