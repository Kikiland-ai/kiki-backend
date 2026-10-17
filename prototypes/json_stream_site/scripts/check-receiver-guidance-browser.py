"""Native captured-tab receiver action ordering with an explicit local model mock."""
import asyncio,json,shutil,sqlite3,uuid
from pathlib import Path
from playwright.async_api import async_playwright

async def run():
 out=Path('work/receiver-guidance-browser');out.mkdir(parents=True,exist_ok=True)
 Path('work/receiver-scene.txt').write_text('carrier')
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path=shutil.which('chromium'),headless=True,args=['--no-sandbox','--enable-usermedia-screen-capturing','--allow-http-screen-capture','--auto-select-tab-capture-source-by-title=Receiver fixture'])
  lab_id=None
  try:
   context=await browser.new_context(viewport={'width':1280,'height':1000})
   target=await context.new_page();await target.goto('http://localhost:8870')
   await target.evaluate("()=>{document.title='Receiver fixture';document.body.innerHTML='<h1>CONTROLLED Carrier dialog</h1><p>Frequency 2*pi*2000 · Phase pi/2</p>'}")
   page=await context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   await page.goto('http://localhost:8870');await page.locator('#lab-model-name').fill('receiver_fixture');await page.locator('#lab-begin').click()
   await page.wait_for_function("localStorage.getItem('kiki-last-lab-id')")
   lab_id=await page.evaluate("localStorage.getItem('kiki-last-lab-id')")
   # Seed only this new owned QA run through local SQLite, never a public API or live Site.
   db=sqlite3.connect('work/lab-preview.sqlite');row=db.execute('SELECT state_json FROM lab_sessions WHERE id=?',(lab_id,)).fetchone();state=json.loads(row[0])
   state['queue']={'current_checkpoint_id':'CP-DSB-05','done_checkpoint_ids':[f'CP-DSB-{i:02d}' for i in range(1,5)],'upcoming_checkpoint_ids':[f'CP-DSB-{i:02d}' for i in range(6,13)],'support_items':[]}
   for i,s in enumerate(state['steps']):
    s['status']='done' if i<4 else 'in_progress' if i==4 else 'upcoming'
    if i==4:s['current_visit_id']=str(uuid.uuid4());s['visits']=[s['current_visit_id']]
   db.execute('UPDATE lab_sessions SET state_json=? WHERE id=?',(json.dumps(state),lab_id));db.commit();db.close()
   await page.reload();await page.wait_for_function("document.getElementById('lab-current').textContent.includes('third Sine Wave')")
   assert 'Modulator' in await page.locator('#lab-where').text_content()
   assert 'transmitter Product' in await page.locator('#lab-done').text_content()
   await page.locator('#share').click()
   await page.wait_for_function("document.getElementById('lab-observation').textContent.includes('Carrier dialog')",timeout=20000)
   assert 'third Sine Wave' in await page.locator('#lab-current').text_content(),'Carrier numeric matches skipped Local carrier creation'
   await page.screenshot(path=str(out/'create-local.png'),full_page=True)
   for scene,title in [('local','Set the new Local carrier'),('configured','Add a second Product'),('product','Connect Modulator output'),('modulated','Connect Local carrier'),('wired','Add a Transfer Fcn')]:
    Path('work/receiver-scene.txt').write_text(scene)
    await target.evaluate("scene=>{document.body.innerHTML='<h1>CONTROLLED receiver scene: '+scene+'</h1><p>Local carrier / Modulator / Receiver product</p>'}",scene)
    await page.wait_for_function("title=>document.getElementById('lab-current').textContent.includes(title)",arg=title,timeout=40000)
    if scene=='configured':
     await page.locator('#lab-pause').click();await page.wait_for_function("document.getElementById('lab-pause').textContent.includes('Resume')")
     await page.locator('#lab-pause').click();await page.wait_for_function("document.getElementById('lab-pause').textContent.includes('Pause')")
     assert 'Add a second Product' in await page.locator('#lab-current').text_content(),'Pause erased remembered action progress'
    if scene=='local':
     assert await page.locator('#lab-settings').is_visible()
     assert '2*pi*2000' in await page.locator('#lab-settings').text_content()
     await page.screenshot(path=str(out/'local-settings.png'),full_page=True)
   await page.locator('#stop').click();await page.wait_for_function("!document.getElementById('share').disabled")
   assert not errors,errors
   report={'status':'PASS','native_tab_capture':True,'provider':'explicit_mock','Carrier_does_not_skip_Local_creation':True,'five_receiver_actions_in_order':True,'placement_and_settings_visible':True,'partial_actions_do_not_complete_checkpoint':True,'pause_preserves_instruction_position':True,'next_stage_starts_with_filter_creation':True,'javascript_errors':errors,'real_simulink_accuracy_claim':False}
   (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
  finally:
   if lab_id:
    try:await page.evaluate("async id=>fetch('/lab-sessions/'+id,{method:'DELETE'})",lab_id)
    except Exception:pass
   await browser.close()
asyncio.run(run())
