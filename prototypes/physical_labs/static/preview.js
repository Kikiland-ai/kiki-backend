import {ApparatusViewer,clampPanel,guidePosition} from './apparatus-viewer.mjs';
import {PreparationClient} from './preparation-client.mjs';
import {componentHint,tooltipPosition} from './component-hints.mjs';
const base='/v1/physical-labs',$=id=>document.getElementById(id);
const DEMO=new URLSearchParams(location.search).get('mode')!=='preparation';
const SESSION_KEY=DEMO?'kiki-physical-experiment-demo':'kiki-physical-preparation';
document.body.classList.toggle('experiment-demo',DEMO);
if(DEMO){$('start').textContent='Start experiment';$('resume').textContent='Resume experiment';document.querySelector('.subtitle').textContent='Connect the trainer. Kiki checks each step. See the outputs as you build.';}
const titles={orientation:'Meet your equipment',prerequisites:'Learn the prerequisites',demonstration:'Watch the procedure',rehearsal:'Your turn at the trainer',observations:'Read the result',faults:'Find the cause',assessment:'Check your preparation',prepared:'Prepared for your college lab'};
const phases=['orientation','prerequisites','demonstration','rehearsal','faults','assessment'];
let state=null,pack=null,latest=null,selected=null,pendingCable=null,explore={},previousActivity='',lastObservation=null,guidePinned=false;
const partButtons=new Map(),markers=new Map();
let tooltipPart=null,tooltipPoint=null,tooltipAnchor=null;
function hidePartTooltip(){
 $('componentTooltip').hidden=true;tooltipAnchor?.removeAttribute('aria-describedby');tooltipPart=null;tooltipPoint=null;tooltipAnchor=null;
}
function showPartTooltip(part,event=null,anchor=null){
 if(!pack||!part){hidePartTooltip();return;}
 tooltipAnchor?.removeAttribute('aria-describedby');tooltipPart=part;tooltipAnchor=anchor;
 if(event&&Number.isFinite(event.clientX)&&Number.isFinite(event.clientY))tooltipPoint=[event.clientX,event.clientY];
 else if(anchor){const r=anchor.getBoundingClientRect();tooltipPoint=[r.right,r.top+r.height/2];}
 if(!tooltipPoint)return;
 const hint=componentHint(part,pack.parts,state?.activity?.step?.rule,pendingCable,state?.activity?.number);
 $('tooltipName').textContent=hint.title;$('tooltipDetail').textContent=hint.detail;$('tooltipCue').textContent=hint.cue;
 $('tooltipStep').textContent=hint.step||'';$('tooltipStep').hidden=!hint.step;
 const tip=$('componentTooltip');tip.classList.toggle('current',hint.current);tip.hidden=false;
 anchor?.setAttribute('aria-describedby','componentTooltip');
 const viewport=$('workspace').querySelector('.viewport'),r=viewport.getBoundingClientRect();
 const left=Math.max(0,-r.left),top=Math.max(0,-r.top);
 const width=Math.min(viewport.clientWidth,window.innerWidth-r.left)-left,height=Math.min(viewport.clientHeight,window.innerHeight-r.top)-top;
 if(width<=0||height<=0){hidePartTooltip();return;}
 tip.style.maxWidth=`${Math.min(290,width-16)}px`;
 const [x,y]=tooltipPosition(tooltipPoint[0]-r.left-left,tooltipPoint[1]-r.top-top,width,height,tip.offsetWidth,tip.offsetHeight);
 tip.style.left=`${x+left}px`;tip.style.top=`${y+top}px`;
}
function refreshPartTooltip(){if(tooltipPart&&!$('componentTooltip').hidden)showPartTooltip(tooltipPart,null,tooltipAnchor);}
function element(tag,value,parent,cls){const n=document.createElement(tag);if(value!==undefined)n.textContent=value;if(cls)n.className=cls;parent?.append(n);return n;}
const local=value=>typeof value==='object'?(value?.[state?.language||$('language').value]||value?.en||''):value;
function button(label,parent,fn,cls='btn'){const b=element('button',label,parent,cls);b.type='button';b.addEventListener('click',fn);return b;}
function showNotice(message){$('notice').textContent=message;}
function feedback(message,error=false){const f=DEMO?$('demoFeedback'):$('feedback');f.className=(DEMO?'guide-feedback':'feedback')+(error?' error':'');f.textContent=message;}
async function api(path,options={}){const response=await fetch(path,{credentials:'same-origin',...options,headers:{'Content-Type':'application/json',...options.headers}});const result=await response.json();if(!response.ok)throw Object.assign(Error(result.detail||`Request failed (${response.status})`),{status:response.status});return result;}
const client=new PreparationClient(api,async s=>{state=s;await render();});
async function send(kind,fields={}){
  $('status').textContent='Saving your progress…';
  if(DEMO){$('demoFeedback').className='guide-feedback checking';$('demoFeedback').textContent=kind==='connect'?'Kiki is checking this connection…':'Kiki is checking this step…';}
  try {const s=await client.event(kind,fields);$('status').textContent=client.pending?'Saving your progress…':'Progress saved';return s;}
  catch(e){feedback(e.message,true);$('status').textContent='Action needs attention';if(e.status===409&&e.message.includes('revision'))showNotice('This session changed in another tab. Resume the saved session before trying again.');return null;}
}
const viewer=new ApparatusViewer($('apparatus'),{
 onPick:p=>selectPart(p),
 onHover:(p,e)=>{$('hoverHelp').textContent=p?`${p.label} · click to inspect${p.kind==='control'?' · shift-drag to turn':''}`:'Click a socket or dial · Drag to rotate · Scroll to zoom';if(p)showPartTooltip(p,e);else hidePartTooltip();},
 onAdjust:(p,delta,commit)=>{const c=pack.controls[p.id];if(!c||typeof c.initial!=='number')return;const range=(c.maximum??1)-(c.minimum??0);explore[p.id]=Math.max(c.minimum??0,Math.min(c.maximum??1,(explore[p.id]??state?.apparatus.controls[p.id]??c.initial)+delta*range));updateViewer();if(commit){renderInspector();if(isCurrentControl(p.id))send('set',{target:p.id,value:explore[p.id],unit:state.activity.step.rule.unit});}},
 onFrame:points=>{for(const p of points){const marker=markers.get(p.id);if(!marker)continue;marker.style.left=`${p.point[0]+16}px`;marker.style.top=`${p.point[1]-15}px`;marker.hidden=!$('showLabels').checked||p.point[0]<0||p.point[0]>$('apparatus').clientWidth||p.point[1]<0||p.point[1]>$('apparatus').clientHeight;}avoidGuideTargets(points);}
});
function updateViewer(){if(!pack)return;const r=state?.activity?.step?.rule,targets=DEMO&&r?[r.target,r.other].filter(Boolean):[];viewer.update({selected,controls:{...Object.fromEntries(Object.entries(pack.controls).map(([k,c])=>[k,c.initial])),...state?.apparatus.controls,...explore},connections:state?.apparatus.connections||[],ghost:pendingCable?null:state?.stage==='demonstration'?r:null,pending:pendingCable,targets,observation:lastObservation});for(const[id,b]of partButtons)b.classList.toggle('selected',id===selected);for(const[id,b]of markers){b.classList.toggle('selected',id===selected);b.classList.toggle('required',targets.includes(id));}refreshPartTooltip();}
async function loadPack(p){hidePartTooltip();pack=p;selected=null;explore={};pendingCable=null;viewer.load(await api(`${base}/assets/${pack.asset}`),pack);buildDirectory();updateViewer();renderInspector();}
async function loadSession(id){const s=await api(`${base}/sessions/${id}`);state=s;client.use(s);lastObservation=null;await loadPack(await api(s.links.pack));localStorage.setItem(SESSION_KEY,id);previousActivity='';await render();}
async function start(){if(client.pending){showNotice('Your current actions are still saving. Try again when they finish.');return;}try{const s=await api(`${base}/sessions`,{method:'POST',headers:{'Idempotency-Key':crypto.randomUUID()},body:JSON.stringify({experiment_id:latest.id,language:$('language').value,mode:DEMO?'experiment_demo':'guided_preparation'})});showNotice('');await loadSession(s.session_id);}catch(e){showNotice(e.message);}}
$('start').onclick=start;
$('resume').onclick=async()=>{const id=localStorage.getItem(SESSION_KEY);if(!id)return showNotice('No experiment demo has been saved in this browser yet.');try{await loadSession(id);showNotice(state.pack_version!==latest.version?'This saved session keeps its earlier equipment model. Start a new experiment for the latest version.':'');}catch(e){showNotice(e.message);}};
$('language').onchange=()=>state?send('language',{value:$('language').value}):renderIntro();
$('showLabels').onchange=()=>updateViewer();
 for(const b of document.querySelectorAll('[data-view]'))b.onclick=()=>{viewer.view(b.dataset.view);for(const p of document.querySelectorAll('[data-view]'))p.classList.toggle('active',p===b);};
for(const b of document.querySelectorAll('[data-phase]'))if(b.id!=='prerequisites')b.disabled=true;
$('prerequisites').onclick=async()=>{if(!state){await start();}if(state?.stage==='orientation')await send('advance');else if(state?.stage==='prerequisites')$('lessonBody').scrollTo({top:0,behavior:'smooth'});else showNotice('Your required concept checks are already complete. Continue with the current preparation step.');};
function buildDirectory(){
 $('parts').replaceChildren();$('hotspots').replaceChildren();partButtons.clear();markers.clear();
 const groups=[['Signal sources',p=>p.id.startsWith('source.')],['Balanced modulator',p=>p.id.startsWith('modulator.')],['Synchronous detector',p=>p.id.startsWith('detector.')],['CRO & power',p=>p.id.startsWith('scope.')||p.id==='trainer.power']];
 const interactive=pack.parts.filter(p=>p.kind!=='body');
 for(const [name,filter]of groups){const group=element('div',undefined,$('parts'),'part-group');element('h3',name,group);for(const p of interactive.filter(filter)){const number=interactive.indexOf(p)+1;const b=button('',group,()=>selectPart(p,true),'part-link');element('span',String(number).padStart(2,'0'),b);element('b',p.label,b);partButtons.set(p.id,b);}}
 for(const [i,p]of interactive.entries()){
  const b=button(String(i+1),$('hotspots'),()=>selectPart(p),'hotspot');b.setAttribute('aria-label',`${p.label} on instrument`);
  b.addEventListener('pointerenter',e=>showPartTooltip(p,e,b));b.addEventListener('pointermove',e=>showPartTooltip(p,e,b));
  b.addEventListener('pointerleave',hidePartTooltip);b.addEventListener('focus',()=>showPartTooltip(p,null,b));b.addEventListener('blur',hidePartTooltip);
  markers.set(p.id,b);
 }
}
function selectPart(p,focus=false){
 selected=p.id;if(focus)viewer.focus(p.id);renderInspector();
 if(state?.stage==='orientation'&&pack.orientation.includes(p.id))send('select',{target:p.id});
 else if(state?.stage==='rehearsal'){
  const rule=state.activity.step.rule;
  if(rule.kind==='select')send('select',{target:p.id});
  else if(rule.kind==='connect'){
   if(p.kind==='output'){pendingCable=p.id;feedback(`${p.label} selected. Now click the destination input socket.`);}
   else if(p.kind==='input'&&pendingCable){const source=pendingCable;pendingCable=null;send('connect',{target:source,other:p.id});}
  }
 }
 updateViewer();
}
function isCurrentControl(id){return state?.stage==='rehearsal'&&state.activity.step.rule.kind==='set'&&state.activity.step.rule.target===id;}
function renderInspector(){
 const container=$('inspector');container.replaceChildren();const p=pack?.parts.find(p=>p.id===selected);
 if(!p){element('strong','Select a socket, dial or switch',container);element('p','Red sockets carry message or output signals; yellow sockets carry carrier/reference signals. Gray dials adjust settings. Read the printed label to identify each connection.',container);return;}
 const head=element('div',undefined,container,'inspector-header');element('span',String(pack.parts.filter(p=>p.kind!=='body').indexOf(p)+1).padStart(2,'0'),head,'part-number');const title=element('div',undefined,head);element('strong',p.label,title);element('div',{input:'Signal input socket',output:'Signal output socket',control:typeof pack.controls[p.id]?.initial==='boolean'?'Power switch':'Adjustable control',display:'Measurement display'}[p.kind]||'Instrument',title,'role');
 element('p',local(p.description),container);
 const control=pack.controls[p.id];if(!control)return;
 const form=element('form',undefined,container,'control');let field;let value=explore[p.id]??state?.apparatus.controls[p.id]??control.initial;
 if(typeof control.initial==='boolean'){field=element('select',undefined,form);for(const [name,v]of [['Off','false'],['On','true']])field.add(new Option(name,v));field.value=String(value);}
 else if(control.choices.length){field=element('select',undefined,form);for(const v of control.choices)field.add(new Option(v,v));field.value=value;}
 else{const slider=element('input',undefined,form);slider.type='range';slider.min=control.minimum??0;slider.max=control.maximum??1;slider.step=p.id.includes('frequency')?p.id.includes('carrier')?500:50:.01;slider.value=value;slider.setAttribute('aria-label',`${p.label} dial`);field=element('input',undefined,form);field.type='number';field.min=slider.min;field.max=slider.max;field.step='any';field.value=value;field.required=true;slider.oninput=()=>{field.value=slider.value;explore[p.id]=Number(slider.value);updateViewer();};field.oninput=()=>{slider.value=field.value;explore[p.id]=Number(field.value);updateViewer();};}
 field.setAttribute('aria-label',`${p.label} value`);if(control.unit)element('span',control.unit,form,'muted');const submit=element('button',isCurrentControl(p.id)?'Apply setting':'Try this control',form,'btn small primary');submit.type='submit';
 form.onsubmit=async e=>{e.preventDefault();value=typeof control.initial==='boolean'?field.value==='true':typeof control.initial==='number'?Number(field.value):field.value;if(isCurrentControl(p.id)){const result=await send('set',{target:p.id,value,unit:state.activity.step.rule.unit});if(result?.feedback?.passed){delete explore[p.id];updateViewer();}}else{explore[p.id]=value;updateViewer();controlNote.textContent=`${p.label}: ${typeof value==='boolean'?(value?'On':'Off'):value}${control.unit?' '+control.unit:''}. This is an exploratory setting.`;}};
 const controlNote=element('p',isCurrentControl(p.id)?'Apply your chosen setting to this procedure step.':'Explore the control here. These trial settings do not count as assessed practice.',container,'muted');controlNote.setAttribute('role','status');
}
function questionForm(parent,questions,target){
 const form=element('form',undefined,parent);for(const [n,q]of questions.entries()){const f=element('fieldset',undefined,form,'question');element('legend',`${n+1}. ${q.prompt}`,f);for(const [key,label]of Object.entries(q.options)){const l=element('label',undefined,f,'option'),input=element('input',undefined,l);input.type='radio';input.name=q.id;input.value=key;input.required=true;element('span',label,l);}}
 const b=element('button','Check my understanding',form,'btn primary');b.type='submit';form.onsubmit=async e=>{e.preventDefault();b.disabled=true;try{await send('answer',{target,answers:Object.fromEntries(new FormData(form).entries())});}finally{b.disabled=false;}};
}
function renderIntro(){if(DEMO){renderDemoIntro();return;}const a=$('activity');a.replaceChildren();element('p','Get familiar with the physical trainer before your college session. You can inspect the apparatus first or start with the concepts.',a);const grid=element('div',undefined,a,'term-list');for(const [n,t]of [['5','prerequisite lessons'],['14','procedure steps'],['3','fault scenarios'],['1','preparation receipt']]){const c=element('div',n,grid);element('small',t,c);}button('Start with prerequisite lessons',a,async()=>{await start();if(state?.stage==='orientation')await send('advance');},'btn primary');}
async function render(){
 if(DEMO){await renderDemo();return;}
 $('stage').textContent=titles[state.stage]||state.stage;$('language').value=state.language;$('status').textContent='Progress saved';
 const passed=Object.values(state.concepts).filter(c=>c.passed).length;$('progress').textContent=state.stage==='prerequisites'?`${passed} of ${pack.concepts.length} concept checks passed. Learn only what this experiment needs.`:`${passed}/${pack.concepts.length} concepts · ${state.step_index} practice actions · ${Object.values(state.faults).filter(f=>f.passed).length}/${pack.faults.length} fault scenarios`;
 $('lessonLabel').textContent=state.stage==='orientation'?'GET TO KNOW THE TRAINER':state.stage==='prerequisites'?'BUILD YOUR UNDERSTANDING':'ONE STEP AT A TIME';
 $('lessonProgress').replaceChildren();for(let i=0;i<pack.concepts.length;i++)element('i',undefined,$('lessonProgress'),i<passed?'passed':'');
 const phase=state.stage==='observations'?'rehearsal':state.stage==='prepared'?'assessment':state.stage;for(const b of document.querySelectorAll('[data-phase]')){b.classList.toggle('current',b.dataset.phase===phase);b.classList.toggle('done',phases.indexOf(b.dataset.phase)<phases.indexOf(phase));if(b.id!=='prerequisites')b.disabled=true;}
 const a=$('activity');a.replaceChildren();const f=$('feedback');f.replaceChildren();f.className='feedback';
 if(state.feedback){if('percent'in state.feedback){element('div',`${state.feedback.percent}% · ${state.feedback.passed?'Check passed':'Revisit the explanation and try again'}`,f);for(const r of state.feedback.results||[])if(!r.correct)element('div',r.feedback,f);}else element('div',state.feedback.message||(state.feedback.passed?'Step completed. Continue below.':''),f);}
 let activityKey=state.stage;
 if(state.stage==='orientation'){
  element('p',local(pack.aim),a);element('p','Inspect any part that interests you. You can begin the prerequisite lessons whenever you are ready.',a);element('p',`${state.orientation_seen.length} of ${pack.orientation.length} suggested parts explored.`,a,'muted');button('Learn prerequisites',a,()=>send('advance'),'btn primary');
 }else if(state.stage==='prerequisites'){
  const c=pack.concepts.find(c=>!state.concepts[c.id]?.passed&&c.depends_on.every(id=>state.concepts[id]?.passed));
  if(c){activityKey+=c.id;element('div',`CONCEPT ${pack.concepts.indexOf(c)+1} / ${pack.concepts.length}`,a,'concept-count');element('h3',c.title,a);element('p',local(c.explanation),a);element('p','Use the highlighted instrument part to connect this idea to the equipment. Pass at least 3 of the 5 questions to continue.',a,'explain');if(previousActivity!==activityKey)selected=c.targets[0];questionForm(a,c.questions,c.id);}
  else{element('p','Your required concept checks are complete. Next, see how the experiment is carried out.',a);button('Watch the demonstration',a,()=>send('advance'),'btn primary');}
 }else if(['demonstration','rehearsal','observations'].includes(state.stage)){
  const step=state.activity.step,rule=step.rule;activityKey+=step.id;if(previousActivity!==activityKey){selected=rule.target;explore={};pendingCable=null;}
  element('div',`${state.stage==='demonstration'?'DEMONSTRATION':'PROCEDURE'} · ${step.id.replaceAll('-',' ').toUpperCase()}`,a,'step-counter');element('h3',local(step.instruction),a);element('p',local(step.why),a,'explain');
  if(state.stage==='demonstration'){element('p',`Step ${state.demonstration_index+1} of ${pack.steps.length}. Follow the marked control or dashed connection. Independent practice comes next.`,a);button('Next demonstration step',a,()=>send('advance'),'btn primary');}
  else if(rule.kind==='select')element('p','Click the named part directly on the instrument, or choose it in the part directory.',a);
  else if(rule.kind==='connect'){
   element('div','Click the output socket, then click the input socket to attach a patch lead.',a,'connection');const form=element('form',undefined,a,'practice');const source=element('select',undefined,form),destination=element('select',undefined,form);source.setAttribute('aria-label','Output terminal');destination.setAttribute('aria-label','Input terminal');for(const p of pack.parts){if(p.kind==='output')source.add(new Option(p.label,p.id));if(p.kind==='input')destination.add(new Option(p.label,p.id));}const b=element('button','Connect terminals',form,'btn primary');b.type='submit';form.onsubmit=e=>{e.preventDefault();send('connect',{target:source.value,other:destination.value});};
  }else if(rule.kind==='set'){element('p','Select the highlighted dial or switch. Try a setting in the control panel below the instrument, then apply it.',a);button('Open this control',a,()=>{selected=rule.target;viewer.focus(selected);renderInspector();updateViewer();$('inspector').scrollIntoView({behavior:'smooth',block:'nearest'});});}
  else{const form=element('form',undefined,a,'practice');const label=element('label',`Your reading (${rule.unit})`,form),input=element('input',undefined,label);input.type='number';input.step='any';input.required=true;input.setAttribute('aria-label','Measured value');const b=element('button','Record virtual reading',form,'btn primary');b.type='submit';form.onsubmit=e=>{e.preventDefault();send('measure',{target:rule.target,other:rule.other,value:Number(input.value),unit:rule.unit});};}
 }else if(state.stage==='faults'){
  const fault=pack.faults.find(f=>!state.faults[f.id]?.passed);if(fault){activityKey+=fault.id;selected=fault.target;element('p','Use the apparatus to reason about the symptom before choosing an answer.',a);questionForm(a,[fault.question],fault.id);}else button('Check preparation readiness',a,()=>send('advance'),'btn primary');
 }else if(state.stage==='assessment')questionForm(a,pack.assessment,'readiness');
 else{element('p','You have completed the theory checks and virtual rehearsal. Take your preparation record to the college lab.',a);const receipt=await api(state.activity.receipt_url);const link=element('a','Download preparation receipt',a,'btn');link.href=URL.createObjectURL(new Blob([JSON.stringify(receipt,null,2)],{type:'application/json'}));link.download='kiki-preparation-receipt.json';}
 if(activityKey!==previousActivity)$('lessonBody').scrollTop=0;previousActivity=activityKey;
 renderInspector();updateViewer();const observations=await api(state.links.observations);lastObservation=observations;drawTraces(observations);updateViewer();
}
function drawTraces(observation){
 for(const canvas of [$('traces'),$('guideTraces')]){
  if(!canvas?.clientWidth)continue;
  const ctx=canvas.getContext('2d'),ratio=Math.min(devicePixelRatio||1,2),height=canvas.id==='guideTraces'?78:130;
  canvas.width=canvas.clientWidth*ratio;canvas.height=height*ratio;ctx.scale(ratio,ratio);const width=canvas.clientWidth;ctx.clearRect(0,0,width,height);ctx.strokeStyle='#34443c';ctx.lineWidth=.5;
  for(let i=1;i<6;i++){ctx.beginPath();ctx.moveTo(0,i*height/6);ctx.lineTo(width,i*height/6);ctx.stroke();}
  for(const [key,color]of [['message_v','#a9bbc0'],['dsb_sc_v','#d0b678'],['recovered_v','#9cbd86']]){const values=observation.traces?.[key];if(!values)continue;ctx.beginPath();ctx.lineWidth=1.2;ctx.strokeStyle=color;values.forEach((v,i)=>{const x=i*width/(values.length-1),y=height/2-v*height*.32;i?ctx.lineTo(x,y):ctx.moveTo(x,y);});ctx.stroke();}
 }
 for(const target of [$('readings'),$('guideReadings')]){
  target.replaceChildren();for(const [label,key,unit]of [['Message','message_frequency_hz','Hz'],['Recovered','recovered_frequency_hz','Hz'],['Peak amplitude','recovered_peak_v','V']]){const div=element('div',label,target);element('strong',`${observation.readings?.[key]??'—'} ${unit}`,div);}
 }
}
function renderDemoIntro(){
 $('kikiGuide').hidden=false;$('guideCounter').textContent='HANDS-ON EXPERIMENT';$('guideInstruction').textContent='Build the DSB-SC signal path';$('guideRoute').replaceChildren();$('guideAction').replaceChildren();
 element('p','The trainer is ready with a 1 kHz message and an 82.5 kHz carrier. Connect the leads, adjust the null control and inspect the recovered signal.', $('guideAction'));
 button('Start experiment', $('guideAction'),start,'btn primary');$('guideWhy').hidden=true;feedback('Kiki will check each action and bring up the next step.');
}
function endpointName(id){const p=pack.parts.find(p=>p.id===id);return p?.label||id;}
function endpointGroup(id){return id.startsWith('source.')?'SIGNAL SOURCE':id.startsWith('modulator.')?'BALANCED MODULATOR':id.startsWith('detector.')?'SYNCHRONOUS DETECTOR':'CRO';}
function demoControl(rule){
 const spec=pack.controls[rule.target],form=element('form',undefined,$('guideAction'),'control');let input;
 const value=state.apparatus.controls[rule.target];
 if(spec.choices.length){input=element('select',undefined,form);for(const v of spec.choices)input.add(new Option(v,v));input.value=value;}
 else if(typeof value==='boolean'){input=element('select',undefined,form);input.add(new Option('Off','false'));input.add(new Option('On','true'));input.value=String(value);}
 else{
  const slider=element('input',undefined,form);slider.type='range';slider.min=spec.minimum??0;slider.max=spec.maximum??1;slider.step=rule.target.includes('frequency')?50:.01;slider.value=value;slider.setAttribute('aria-label',`${endpointName(rule.target)} dial`);
  input=element('input',undefined,form);input.type='number';input.step='any';input.min=slider.min;input.max=slider.max;input.required=true;input.value=value;input.setAttribute('aria-label',`${endpointName(rule.target)} value`);
  slider.oninput=()=>{input.value=slider.value;explore[rule.target]=Number(slider.value);updateViewer();};input.oninput=()=>{slider.value=input.value;explore[rule.target]=Number(input.value);updateViewer();};
 }
 if(spec.unit)element('span',spec.unit,form,'muted');const b=element('button','Apply setting',form,'btn primary');b.type='submit';form.onsubmit=async e=>{e.preventDefault();b.disabled=true;const v=typeof value==='boolean'?input.value==='true':typeof value==='number'?Number(input.value):input.value;try{await send('set',{target:rule.target,value:v,unit:rule.unit});}finally{b.disabled=false;}};
}
async function renderDemo(){
 $('kikiGuide').hidden=false;$('status').textContent='Progress saved';$('guideRoute').replaceChildren();$('guideAction').replaceChildren();
 lastObservation=await api(state.links.observations);
 if(state.stage==='experiment_complete'){
  $('guideCounter').textContent='EXPERIMENT COMPLETE';$('guideInstruction').textContent='Your message has been recovered';$('guideWhy').hidden=true;
  const result=await api(state.activity.result_url);element('p',`${result.completed_steps} steps checked. Compare the original message with the recovered waveform.`, $('guideAction'),'guide-complete');
  element('p',`Recovered: ${result.readings.recovered_frequency_hz} Hz · ${result.readings.recovered_peak_v} V peak in this ideal model.`, $('guideAction'));
  button('Run the experiment again', $('guideAction'),start,'btn primary');feedback('All connections, the null setting and output readings were checked.');selected='scope.display';updateViewer();drawTraces(lastObservation);return;
 }
 const step=state.activity.step,rule=step.rule,key=step.id;
 if(previousActivity!==key){selected=rule.target;pendingCable=null;explore={};viewer.view(rule.kind==='measure'?'scope':rule.kind==='connect'&&(rule.target.startsWith('scope.')||rule.other?.startsWith('scope.'))?'all':'trainer');}
 previousActivity=key;
 $('guideCounter').textContent=`STEP ${state.activity.number} OF ${state.activity.total}`;$('guideInstruction').textContent=step.instruction.en;
 $('guideWhy').hidden=false;$('guideReason').textContent=local(step.why);
 if(state.feedback?.passed){const previous=pack.steps.find(s=>s.id===state.feedback.step_id);feedback(previous?.rule.kind==='connect'?'Connection checked. Next step is ready.':'Step checked. Next step is ready.');}
 else if(state.feedback?.passed===false)feedback(rule.kind==='connect'?'That is not the required connection. Use the two highlighted sockets for this step.':state.feedback.message||'Not yet. Check this setting or reading.',true);
 else feedback(rule.kind==='connect'?'Select the output socket, then the input socket. Kiki will check the lead.':'Use the highlighted control or read the output below.');
 if(rule.kind==='connect'){
  for(const [i,id]of [rule.target,rule.other].entries()){
   if(i)element('span','→',$('guideRoute'));
   const chip=element('div',undefined,$('guideRoute'),'endpoint');element('small',endpointGroup(id),chip);element('strong',endpointName(id),chip);
  }
 }else if(rule.kind==='set')demoControl(rule);
 else if(rule.kind==='measure'){
  const form=element('form',undefined,$('guideAction'),'control'),label=element('label',`Observed value (${rule.unit})`,form),input=element('input',undefined,label);input.type='number';input.step='any';input.required=true;input.value=lastObservation.readings?.[rule.other]??'';input.setAttribute('aria-label','Observed virtual reading');
  const b=element('button','Record reading',form,'btn primary');b.type='submit';form.onsubmit=e=>{e.preventDefault();send('measure',{target:rule.target,other:rule.other,value:Number(input.value),unit:rule.unit});};
 }else element('p','Select the highlighted part on the trainer.', $('guideAction'));
 updateViewer();drawTraces(lastObservation);
}
// The guide is part of the workspace: it remains usable in native fullscreen.
const workspace=$('workspace'),floater=$('kikiGuide'),dragHandle=$('guideDrag');let guideDrag=null;
function avoidGuideTargets(points){
 if(!DEMO||guidePinned||guideDrag||floater.hidden||!state?.activity?.step)return;
 const rule=state.activity.step.rule,ids=[rule.target,rule.other],targets=points.filter(p=>ids.includes(p.id)).map(p=>[p.point[0]+16,p.point[1]-15]);
 const viewport=workspace.querySelector('.viewport'),r=viewport.getBoundingClientRect(),p=floater.getBoundingClientRect();
 const position=guidePosition(targets,viewport.clientWidth,viewport.clientHeight,p.width,p.height,[p.left-r.left,p.top-r.top]);
 positionGuide(position[0],position[1]);
}
function positionGuide(x,y){const r=workspace.querySelector('.viewport'),p=clampPanel(x,y,r.clientWidth,r.clientHeight,floater.offsetWidth,floater.offsetHeight);floater.style.left=`${p[0]}px`;floater.style.top=`${p[1]}px`;floater.style.right='auto';}
dragHandle.addEventListener('pointerdown',e=>{guidePinned=true;const p=floater.getBoundingClientRect(),r=workspace.querySelector('.viewport').getBoundingClientRect();guideDrag={x:e.clientX,y:e.clientY,left:p.left-r.left,top:p.top-r.top};dragHandle.setPointerCapture(e.pointerId);});
dragHandle.addEventListener('pointermove',e=>{if(guideDrag)positionGuide(guideDrag.left+e.clientX-guideDrag.x,guideDrag.top+e.clientY-guideDrag.y);});
dragHandle.addEventListener('pointerup',()=>guideDrag=null);dragHandle.addEventListener('pointercancel',()=>guideDrag=null);
dragHandle.addEventListener('keydown',e=>{const moves={ArrowLeft:[-20,0],ArrowRight:[20,0],ArrowUp:[0,-20],ArrowDown:[0,20]};if(e.key==='Home'){guidePinned=false;floater.style.left='';floater.style.top='';floater.style.right='';viewer.schedule();return;}if(moves[e.key]){guidePinned=true;e.preventDefault();const p=floater.getBoundingClientRect(),r=workspace.querySelector('.viewport').getBoundingClientRect();positionGuide(p.left-r.left+moves[e.key][0],p.top-r.top+moves[e.key][1]);}});
$('guideCollapse').onclick=()=>{const body=$('guideBody');body.hidden=!body.hidden;$('guideCollapse').textContent=body.hidden?'+':'−';$('guideCollapse').setAttribute('aria-expanded',String(!body.hidden));$('guideCollapse').setAttribute('aria-label',body.hidden?'Expand Kiki guide':'Collapse Kiki guide');if(!body.hidden&&lastObservation)drawTraces(lastObservation);};
function fullscreenState(){const active=document.fullscreenElement===workspace||workspace.classList.contains('expanded');$('fullscreenLabel').textContent=active?'Exit fullscreen':'Fullscreen';$('fullscreen').setAttribute('aria-label',active?'Exit fullscreen':'Enter fullscreen');$('fullscreen').setAttribute('aria-pressed',String(active));if(floater.style.left){const r=workspace.querySelector('.viewport');positionGuide(parseFloat(floater.style.left),parseFloat(floater.style.top));}viewer.schedule();if(lastObservation)drawTraces(lastObservation);}
$('fullscreen').onclick=async()=>{try{if(document.fullscreenElement===workspace)await document.exitFullscreen();else if(workspace.classList.contains('expanded'))workspace.classList.remove('expanded');else if(workspace.requestFullscreen)await workspace.requestFullscreen();else workspace.classList.add('expanded');}catch(e){workspace.classList.toggle('expanded');}fullscreenState();};
document.addEventListener('fullscreenchange',fullscreenState);document.addEventListener('keydown',e=>{if(e.key==='Escape'&&workspace.classList.contains('expanded')){workspace.classList.remove('expanded');fullscreenState();}});

(async()=>{try{const list=await api(`${base}/experiments`);latest=list[0];if(!latest)throw Error('No prescribed experiments are available.');for(const e of list)$('experiment').add(new Option(e.title,e.id));await loadPack(await api(`${base}/experiments/${latest.id}`));renderIntro();const id=localStorage.getItem(SESSION_KEY);if(id){const saved=await api(`${base}/sessions/${id}`).catch(()=>null);if(saved?.pack_version===latest.version&&(!DEMO||saved.mode==='experiment_demo'))await loadSession(id);else if(saved)showNotice('Start a new experiment to use the latest setup. Your earlier session remains saved.');}}catch(e){showNotice(e.message);}})();

$('workspace').querySelector('.viewport').addEventListener('pointerleave',hidePartTooltip);
window.addEventListener('scroll',hidePartTooltip,true);
document.addEventListener('fullscreenchange',hidePartTooltip);
document.addEventListener('keydown',e=>{if(e.key==='Escape')hidePartTooltip();});
