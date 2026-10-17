"""Native tab sharing with a declared fixture model; no real Simulink recognition."""
import argparse,asyncio,json,shutil
from pathlib import Path
from playwright.async_api import async_playwright
async def check(args):
 out=Path(args.output_dir);out.mkdir(parents=True,exist_ok=True)
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path=shutil.which('chromium'),headless=True,args=['--no-sandbox','--enable-usermedia-screen-capturing','--allow-http-screen-capture','--auto-select-tab-capture-source-by-title=Kiki guided fixture'])
  try:
   context=await browser.new_context(viewport={'width':1280,'height':1000})
   target=await context.new_page();await target.goto(args.url)
   await target.evaluate("""()=>{document.title='Kiki guided fixture';document.body.innerHTML='<main><h1>CONTROLLED Simulink-shaped fixture</h1><p>Model dsb_sc_test</p><p>Message | Carrier | Product</p></main>';}""")
   page=await context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   await page.goto(args.url);await page.locator('#lab-model-name').fill('dsb_sc_test');await page.locator('#lab-begin').click()
   await page.wait_for_function("!document.getElementById('lab-run').hidden")
   assert await page.locator('#lab-criteria input').count()==0,'Checklist input survived the redesign'
   assert not await page.locator('#lab-criteria').is_visible(),'Internal criteria are in the main flow'
   if args.quota_fixture:
    failed=[False]
    async def transient_capture(route):
     if not failed[0]:
      failed[0]=True;await route.fulfill(status=503,json={'detail':'Controlled transient receiver failure','retry_after_ms':2000})
     else:await route.continue_()
    await page.route('**/screen-sessions/*/frame',transient_capture)
   await page.locator('#share').click()
   await page.wait_for_function("document.getElementById('lab-observation').textContent.includes('Controlled Simulink-shaped')",timeout=20000)
   await page.wait_for_function("!document.getElementById('lab-confirmation').hidden",timeout=30000)
   await page.locator('#lab-confirm').click()
   await page.wait_for_function("document.getElementById('lab-current').textContent.includes('name it Message')",timeout=12000)
   if args.quota_fixture:
    await page.wait_for_function("document.getElementById('lab-watch-state').textContent.includes('ANALYSIS RETRY')",timeout=20000)
    before=await page.locator('#count').text_content()
    await page.wait_for_timeout(5000)
    assert int(await page.locator('#count').text_content())>int(before),'Capture stopped during provider cooldown'
    assert await page.locator('#stop').is_enabled()
   # No check/review/continue click on the visible block-placement step.
   await page.wait_for_function("document.getElementById('lab-current').textContent.includes('Set the Message signal to 100 Hz')",timeout=110000 if args.quota_fixture else 40000)
   state=await page.evaluate("""async key=>{const id=localStorage.getItem(key);return(await fetch('/lab-sessions/'+id)).json();}""",args.storage_key)
   assert state['queue']['done_checkpoint_ids']==['CP-DSB-01','CP-DSB-02']
   tracked_step=state['steps'][1] if isinstance(state['steps'],list) else state['steps']['CP-DSB-02']
   assert tracked_step['completion_basis']=='screen_inferred_or_student_report'
   assert tracked_step['assessment_status']=='unassessed'
   assert all(c['understanding']=='unknown' for c in state['learner_state']['concepts'])
   assert await page.locator('#lab-where').text_content()=='Double-click the block labelled Message.'
   assert await page.locator('#lab-settings').is_visible()
   assert '2*pi*100' in await page.locator('#lab-settings').text_content()
   assert 'Tracked earlier' in await page.locator('#lab-done').text_content()
   await page.screenshot(path=str(out/'guided.png'),full_page=True)
   await page.locator('#lab-correction').click()
   await page.wait_for_function("document.getElementById('lab-status').textContent.includes('reset this step')")
   await page.locator('#stop').click();await page.wait_for_function("!document.getElementById('share').disabled")
   await page.reload();await page.wait_for_function("document.getElementById('lab-current').textContent.includes('Set the Message signal to 100 Hz')")
   assert not errors,errors
   report={'status':'PASS','native_capture':True,'source':'controlled_fixture_tab','model':'explicit_local_mock','automatic_observation':True,'automatic_visible_step_advancement':True,'save_requires_explicit_report':True,'visible_checklist_removed':True,'correction_and_reload':True,'javascript_errors':errors,'real_simulink_recognition':False,'provider_cooldown_and_capture_retry':args.quota_fixture}
   (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
   await page.evaluate("""async key=>{const id=localStorage.getItem(key);await fetch('/lab-sessions/'+id,{method:'DELETE'});localStorage.removeItem(key);}""",args.storage_key)
  finally:await browser.close()
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--quota-fixture',action='store_true')
parser.add_argument('--url',default='http://localhost:8870')
parser.add_argument('--storage-key',default='kiki-last-lab-id')
parser.add_argument('--output-dir',default='work/guided-browser')
asyncio.run(check(parser.parse_args()))
