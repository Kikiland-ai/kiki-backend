"""Native controlled tab capture + explicit mock lab observer. No real Simulink claim."""
import asyncio,json,shutil
from pathlib import Path
from playwright.async_api import async_playwright
async def check():
 out=Path('work/lab-browser-check');out.mkdir(parents=True,exist_ok=True)
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path=shutil.which('chromium'),headless=True,args=['--no-sandbox','--enable-usermedia-screen-capturing','--allow-http-screen-capture','--auto-select-tab-capture-source-by-title=Kiki DSB fixture'])
  try:
   ctx=await browser.new_context(viewport={'width':1280,'height':1000})
   target=await ctx.new_page();await target.goto('http://localhost:8870')
   await target.evaluate("""()=>{document.title='Kiki DSB fixture';document.body.innerHTML='<main><h1>Simulink-shaped test fixture: dsb_sc_test</h1><p>Message | Carrier | Modulator | Local carrier | Receiver product | Lowpass | Recovery gain | Inputs | Modulated | Recovery comparison</p><p>Message frequency: 2*pi*100 rad/s; Local Phase: pi/2</p></main>';}""")
   page=await ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   await page.goto('http://localhost:8870');await page.locator('#lab-model-name').fill('dsb_sc_test');await page.locator('#lab-operator').check();await page.locator('#lab-begin').click()
   await page.wait_for_function("!document.getElementById('lab-run').hidden")
   await page.locator('#share').click();await page.wait_for_function("Number(document.getElementById('count').textContent)>=2",timeout=16000)
   assert not await page.locator('#enable-analysis').is_checked(),'Generic auto analysis was not disabled for deliberate lab checks'
   await page.locator('#lab-check').click()
   try: await page.wait_for_function("document.getElementById('lab-observation').textContent.includes('Controlled Simulink-shaped')",timeout=15000)
   except Exception:
    print(json.dumps({'lab_status':await page.locator('#lab-status').inner_text(),'errors':errors}))
    raise
   await page.wait_for_function("document.getElementById('lab-checked').naturalWidth>0")
   for box in await page.locator('#lab-criteria input').all():await box.check()
   await page.wait_for_timeout(2500)
   assert await page.locator('#lab-criteria input:checked').count()==2,'Frame arrivals cleared user selection'
   await page.locator('#lab-review-note').fill('Reviewed the controlled fixture title and its saved model reference.')
   await page.locator('#lab-review').click();await page.wait_for_function("document.getElementById('lab-current').textContent.startsWith('2.')")
   assert '1 / 12' in await page.locator('#lab-progress').inner_text()
   await page.locator('#stop').click();await page.wait_for_function("!document.getElementById('share').disabled")
   await page.reload();await page.wait_for_function("document.getElementById('lab-current').textContent.startsWith('2.')")
   await page.locator('#share').click();await page.wait_for_function("Number(document.getElementById('count').textContent)>=2",timeout=15000)
   assert await page.locator('#lab-current').inner_text()=='2. Place the Message and Carrier sources'
   await page.locator('#lab-entry-type').select_option('help');await page.locator('#lab-answer').fill('How do I locate the Sine Wave block?');await page.locator('#lab-save-answer').click()
   await page.wait_for_function("document.getElementById('lab-status').textContent.includes('Response saved')")
   with_export=await page.evaluate("""async()=>{const id=localStorage.getItem('kiki-last-lab-id');return {state:await(await fetch('/lab-sessions/'+id)).json(),events:await(await fetch('/lab-sessions/'+id+'/events')).json()};}""")
   assert with_export['state']['queue']['done_checkpoint_ids']==['CP-DSB-01']
   assert with_export['state']['workspace']['capture_epoch']>=2
   assert any(e['event_type']=='lab_help' for e in with_export['events'])
   await page.screenshot(path=str(out/'lab.png'),full_page=True)
   await page.locator('#stop').click();await page.wait_for_function("!document.getElementById('share').disabled")
   assert not errors,errors
   report={'status':'PASS','source':'controlled_simulink_shaped_fixture','model':'explicit_local_mock','native_capture':True,
    'reviewed_queue_advance':True,'frame_arrivals_preserve_selection':True,'reload_resume_with_new_capture_epoch':True,'question_event_recorded':True,'javascript_errors':errors}
   (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
  finally:await browser.close()
asyncio.run(check())
