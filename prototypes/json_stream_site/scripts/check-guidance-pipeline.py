"""Local vertical-slice QA: native getDisplayMedia -> actual reader/Worker ->
actual broker/consumer/compositor -> visible pixels + persisted exposure ACK.
Chrome APIs/message dispatch and model localization are explicit fixtures.
This does NOT establish installed-extension or real Simulink acceptance.
Start scripts/serve-guidance-fixture.mjs first. No production calls are made.
"""
import asyncio,base64,json,tempfile,sys,hashlib,subprocess
from pathlib import Path
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[3]
ASSETS=Path(__file__).resolve().parents[1]/'assets'
ADAPTER=ROOT/'prototypes/screen_writing/shared_tab'
ORIGIN='https://kiki-screen-receiver.woodsycarp256.chatgpt.site'
SOURCE='https://matlab.mathworks.com/controlled-writer-fixture'
async def main():
 async with async_playwright() as p:
  tls='--tls' in sys.argv
  origin='https://localhost' if tls else ORIGIN
  args=['--no-sandbox','--enable-usermedia-screen-capturing','--auto-select-tab-capture-source-by-title=Kiki complete writer fixture']
  if tls:
   public=subprocess.check_output(['openssl','x509','-pubkey','-noout','-in',str(ROOT/'work/guidance-integration/tls/cert.pem')])
   der=subprocess.check_output(['openssl','pkey','-pubin','-outform','DER'],input=public)
   args+=['--ignore-certificate-errors-spki-list='+base64.b64encode(hashlib.sha256(der).digest()).decode()]
  profile=tempfile.TemporaryDirectory(prefix='kiki-guidance-native-')
  context=await p.chromium.launch_persistent_context(profile.name,executable_path='/usr/bin/chromium',headless=True,viewport={'width':1200,'height':800},args=args)
  browser=context
  fault={'enabled':'--invalidate-before-paint' in sys.argv,'injected':False}
  errors=[];target=await context.new_page();reader=await context.new_page();broker=await context.new_page()
  async def worker_route(route):
   req=route.request
   response=await context.request.fetch('http://127.0.0.1:8872'+req.url[len(ORIGIN):],method=req.method,headers=req.headers,data=req.post_data_buffer,timeout=30000)
   await route.fulfill(response=response)
  if not tls:await context.route(ORIGIN+'/**',worker_route)
  await target.route(SOURCE,lambda r:r.fulfill(content_type='text/html',body='''<!doctype html><title>Kiki complete writer fixture</title><style>body{margin:0;background:#fafafa;font:18px system-ui}input{position:fixed;box-sizing:border-box;left:25vw;top:32.5vh;width:18vw;height:7vh}</style><h1>Controlled Message settings</h1><input id=frequency value="2*pi*100">'''))
  await broker.route('https://broker.fixture/**',lambda r:r.fulfill(body='<title>Explicit Chrome API fixture</title>'))
  await target.goto(SOURCE);await broker.goto('https://broker.fixture/')
  async def broker_call(m,sender):
   return await broker.evaluate('async ({m,sender})=>{try{return await fixtureHandle(m,sender)}catch(e){return {error:e.message}}}',{'m':m,'sender':sender})
  async def runtime(source,m):
   page=source['page'];sender={'url':page.url,'tab':{'id':10 if page==target else 20}}
   return await broker_call(m,sender)
  async def dispatch(source,tab,m):
   page=target if tab==10 else reader
   if m.get('to')=='controller':
    await page.evaluate('m=>window.fixtureRuntimeListener?.(m)',m);return {}
   if tab==10 and m.get('type')=='commit' and fault['enabled'] and not fault['injected']:
    fault['injected']=True
    await target.locator('#frequency').evaluate("el=>el.style.left='45vw'")
    await target.wait_for_timeout(30)
   return await page.evaluate('m=>new Promise(resolve=>window.fixtureRuntimeListener(m,{},resolve))',m)
  async def inject(source,m):
   if m.get('files'):
    for name in m['files']:await target.add_script_tag(path=str(ADAPTER/name))
    return [{'result':True}]
   result=await target.evaluate('({code,args})=>(0,eval)("("+code+")")(...args)',{'code':m['code'],'args':m.get('args',[])})
   return [{'result':result}]
  await context.expose_binding('fixtureRuntime',runtime);await broker.expose_binding('fixtureDispatch',dispatch);await broker.expose_binding('fixtureInject',inject)
  runtime_js="window.chrome={runtime:{sendMessage:m=>fixtureRuntime(m),onMessage:{addListener:fn=>{window.fixtureRuntimeListener=fn}}}};"
  await target.evaluate(runtime_js)
  await reader.add_init_script(runtime_js+(ADAPTER/'bridge.js').read_text().replace(ORIGIN,origin))
  async def focus(source):await target.bring_to_front()
  await reader.expose_binding('fixtureFocusTarget',focus)
  await reader.add_init_script("const nativeShare=navigator.mediaDevices.getDisplayMedia.bind(navigator.mediaDevices);navigator.mediaDevices.getDisplayMedia=async options=>{const stream=await nativeShare(options);await fixtureFocusTarget();return stream;};")
  await broker.evaluate("""()=>{window.store={};window.chrome={runtime:{getManifest:()=>({version:'0.4.0'}),getURL:p=>'chrome-extension://fixture/'+p,onMessage:{addListener(){}},sendMessage:async()=>({})},storage:{session:{get:async()=>store,set:async o=>Object.assign(store,o)}},tabs:{get:async()=>({id:10,url:'https://matlab.mathworks.com/controlled-writer-fixture',title:'MATLAB fixture'}),sendMessage:(id,m)=>fixtureDispatch(id,m),onRemoved:{addListener(){}},onUpdated:{addListener(){}}},scripting:{executeScript:m=>fixtureInject({files:m.files,code:m.func?.toString(),args:m.args})},commands:{onCommand:{addListener(){}}}};}""")
  for name in ['demo.js','frame-probe.js','guidance-protocol.js']:await broker.add_script_tag(path=str(ADAPTER/name))
  await broker.evaluate("window.importScripts=()=>{}")
  await broker.evaluate('(()=>{'+(ADAPTER/'background.js').read_text().replace(ORIGIN,origin)+';window.fixtureHandle=handle;})()')
  await target.bring_to_front()
  connected=await broker_call({'type':'start','tabId':10,'mode':'tutor'},{'url':'chrome-extension://fixture/popup.html'})
  assert connected.get('connected'),connected
  reader.on('pageerror',lambda e:errors.append(str(e)))
  await reader.goto(origin);await reader.locator('#lab-model-name').fill('controlled_dsb_fixture');await reader.locator('#lab-begin').click()
  await reader.wait_for_function("document.querySelector('#lab-run').hidden===false")
  await reader.locator('#share').click()
  try:
   streamed_panel=False
   if tls:
    await reader.wait_for_function("document.querySelector('#lab-stream-findings').children.length>0",polling=50,timeout=20000)
    panel=await reader.locator('#lab-observation').text_content()
    assert await reader.evaluate('KikiWriting.diagnostics.health.painted')==0
    await reader.wait_for_function("Number(document.querySelector('#count').textContent)>=2",polling=50,timeout=10000)
    assert await reader.locator('#lab-observation').text_content()==panel
    streamed_panel=True
   if '--expect-clock-rejection' in sys.argv:
    await reader.wait_for_function("KikiWriting.diagnostics.events.some(e=>e.stage==='delivery_rejected'&&e.reason.includes('Clock uncertainty'))",timeout=45000)
    diag=await reader.evaluate('KikiWriting.diagnostics');assert diag['health']['painted']==0,diag
    await reader.wait_for_timeout(150)
    evidence=await (await context.request.get('http://127.0.0.1:8872/__fixture/evidence')).json()
    out=ROOT/'work/guidance-timing/clock-before';out.mkdir(parents=True,exist_ok=True)
    report={'status':'PASS','expected_fault':'server_processing_counted_as_clock_uncertainty','no_paint_ack':True,'consumer':diag}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='consumer'},indent=2));return
   if fault['enabled']:
    await reader.wait_for_function("KikiWriting.diagnostics.events.some(e=>e.stage==='delivery_rejected')",timeout=45000)
    await reader.wait_for_timeout(150)
    diag=await reader.evaluate('KikiWriting.diagnostics')
    assert fault['injected'] and diag['health']['painted']==0,diag
    evidence=await (await context.request.get('http://127.0.0.1:8872/__fixture/evidence')).json()
    assert any(a['status']=='rejected' for a in evidence['acks']),evidence
    out=ROOT/'work/guidance-integration/native-negative';out.mkdir(parents=True,exist_ok=True)
    report={'status':'PASS','fault':'view_invalidated_between_verification_and_paint','no_paint_ack':True,'reject_ack_persisted':True,'consumer':diag}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');(out/'worker-evidence.json').write_text(json.dumps(evidence,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='consumer'},indent=2));return
   await reader.wait_for_function('KikiWriting.diagnostics.health.painted>0',timeout=45000)
   readable='--check-readable' in sys.argv
   if readable:await reader.wait_for_timeout(1500)
   diag=await reader.evaluate('KikiWriting.diagnostics')
   cdp=await context.new_cdp_session(target);png=base64.b64decode((await cdp.send('Page.captureScreenshot',{'format':'png'}))['data'])
   out=ROOT/'work/guidance-integration/native';out.mkdir(parents=True,exist_ok=True);(out/'pipeline-painted.png').write_bytes(png)
   from PIL import Image
   import io
   image=Image.open(io.BytesIO(png));pixels=[image.getpixel((300+dx,288))[:3] for dx in range(-3,4)]
   assert any(b>160 and b>r+80 for r,g,b in pixels),pixels
   await reader.wait_for_function("KikiWriting.diagnostics.events.some(e=>e.stage==='ack_recorded')",timeout=4000)
   diag=await reader.evaluate('KikiWriting.diagnostics');logs=await broker_call({'type':'diagnostics'},{'url':'chrome-extension://fixture/popup.html'})
   assert any(e['stage']=='guidance_painted' for e in logs['events']),logs
   assert diag['health']['captured']>=2,diag
   assert not errors,errors
   evidence=await (await context.request.get('http://127.0.0.1:8872/__fixture/evidence')).json()
   (out/'worker-evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
   assert any(a['status']=='live_rendered' for a in evidence['acks']),evidence
   assert await reader.evaluate('document.querySelector("#preview").srcObject.getVideoTracks()[0].getCaptureHandle()!==null')
   report={'status':'PASS','native_screen_capture':True,'real_browser_sse_stream':tls,'controller_origin_is_local_fixture_override':tls,'coherent_panel_during_stream':streamed_panel,'reader_visibility_at_paint':await reader.evaluate('document.visibilityState'),'actual_reader_worker_broker_consumer_compositor':True,'blue_pixels_at_authored_control':True,'visible_after_1500ms':readable,'persisted_exposure_ack':True,'periodic_frames_during_delayed_analysis':diag['health']['captured'],'installed_extension_tested':False,'real_simulink_tested':False,'real_model_localization_tested':False,'consumer':diag}
   (out/'pipeline-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='consumer'},indent=2))
  except:
   print('CONSUMER',await reader.evaluate('KikiWriting.diagnostics'),flush=True)
   print('BROKER',await broker_call({'type':'diagnostics'},{'url':'chrome-extension://fixture/popup.html'}),flush=True)
   print('LAB',await reader.locator('#lab-status').text_content(),flush=True)
   raise
  finally:await browser.close();profile.cleanup()
asyncio.run(main())
