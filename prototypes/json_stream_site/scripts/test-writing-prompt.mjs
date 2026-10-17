import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {drawingWritingPrompt,LIVE_DRAWING_PROMPT_VERSION} from '../worker/guidance-prompt.js';
import {validateDrawingModel} from '../worker/guidance.js';
const data=JSON.parse(readFileSync(new URL('./fixtures/generated-gain-guidance.json',import.meta.url))),definition=JSON.parse(readFileSync(new URL('../data/experiment.json',import.meta.url))),policy=JSON.parse(readFileSync(new URL('../data/guided-policy.json',import.meta.url))),cp=definition.checkpoints.find(c=>c.id===data.checkpoint_id);
const actions=data.eligible_actions;
function response(candidate){return {criteria:cp.completion_criteria.map(c=>({criterion_id:c.id,status:'unknown',evidence:'Fixture; no visual claim.'})),action_findings:policy.procedures[cp.id].map(a=>({action_id:a.id,status:'unknown',evidence:'Fixture; no visual claim.'})),uncertainties:[],screen_guidance:[candidate]};}
const check=value=>validateDrawingModel(value,{eligible_actions:actions},cp,policy.procedures[cp.id]);
test('offered-key and hidden-target prompt examples satisfy the independent full contract',()=>{
 const prompt=drawingWritingPrompt(actions),line=prefix=>JSON.parse(prompt.split('\n').find(l=>l.startsWith(prefix)).slice(prefix.length));
 const mark=line('Valid text mark: '),candidate={action_id:actions[0].action_id,mode:'annotate',targets:[{target_id:actions[0].required_target_ids[0],status:'resolved',region:{x:.2,y:.3,width:.4,height:.1}}],marks:[mark]};
 assert.doesNotThrow(()=>check(response(candidate)));assert.doesNotThrow(()=>check(response(line('Valid candidate when all required controls are hidden: '))));
 candidate.marks=[line('Invalid text mark: ')];assert.throws(()=>check(response(candidate)),/schema_oneOf/);
});
test('missing anchor, prose references and another action reference remain rejected',()=>{
 const mark={kind:'text',cue_id:'note',anchor:{target_id:'recovery_gain.value',u:0,v:1},text_ref:'action_title'},candidate={action_id:actions[0].action_id,mode:'annotate',targets:[{target_id:'recovery_gain.value',status:'resolved',region:{x:.2,y:.3,width:.4,height:.1}}],marks:[mark]};
 for(const bad of [{kind:'text',cue_id:'note',text_ref:'action_title'},{...mark,text_ref:'Gain is set to 2'},{...mark,text_ref:'other_action_key'},{...mark,anchor:{target_id:'workspace.canvas',u:0,v:1}}]){candidate.marks=[bad];assert.throws(()=>check(response(candidate)));}
});
test('two-target abstention example preserves all required targets and contains no guessed geometry',()=>{
 const action={...actions[0],required_target_ids:['lowpass.numerator','lowpass.denominator']},prompt=drawingWritingPrompt([action]),prefix='Valid candidate when all required controls are hidden: ',c=JSON.parse(prompt.split('\n').find(l=>l.startsWith(prefix)).slice(prefix.length));
 assert.deepEqual(c.targets,action.required_target_ids.map(target_id=>({target_id,status:'unresolved',region:null})));assert.deepEqual(c.marks,[]);assert.match(prompt,new RegExp(LIVE_DRAWING_PROMPT_VERSION.replaceAll('.','\\.')));
});
