import test from 'node:test';
import assert from 'node:assert/strict';
import {verificationCadence} from '../assets/lab-cadence.js';
const policy={fast_interval_ms:3000,idle_interval_ms:12000};
test('changed screen or checkpoint and pending distinct-frame confirmation use the fast cadence',()=>{
 for(const facts of [{sameFrame:false},{sameFrame:true,pendingSecondRead:true},{sameFrame:true,evidenceExpiring:true}])assert.equal(verificationCadence({...facts,status:'available'},policy),3000);
});
test('stable supported screen is skipped; provider-wait stays bounded by idle cadence and external deadline',()=>{
 assert.equal(verificationCadence({sameFrame:true,status:'available'},policy),null);
 assert.equal(verificationCadence({sameFrame:true,status:'waiting_for_provider'},policy),12000);
});
test('deployed assets load the cadence helper as a module',async()=>{
 const {default:worker}=await import('../dist/server/index.js');
 const page=await worker.fetch(new Request('https://receiver.test/'),{});
 assert.match(await page.text(),/<script type="module" src="\/static\/lab.js"/);
 const helper=await worker.fetch(new Request('https://receiver.test/static/lab-cadence.js'),{});
 assert.equal(helper.status,200);assert.match(helper.headers.get('Content-Type'),/javascript/);assert.match(await helper.text(),/export function verificationCadence/);
});
