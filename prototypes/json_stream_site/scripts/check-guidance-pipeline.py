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
  def option(name):return sys.argv[sys.argv.index(name)+1] if name in sys.argv else None
  source_image=Path(option('--source-image')).resolve() if option('--source-image') else None
  switch_image=Path(option('--switch-image')).resolve() if option('--switch-image') else None
  custom_out=Path(option('--output-dir')).resolve() if option('--output-dir') else None
  expected_region=json.loads(option('--expected-region')) if option('--expected-region') else None
  expect_text_only='--expect-text-only' in sys.argv
  tls='--tls' in sys.argv
  live_gain='--live-gain' in sys.argv
  high_resolution='--high-resolution' in sys.argv
  viewport={'width':1848,'height':1014} if high_resolution else {'width':1200,'height':800}
  if source_image:
   from PIL import Image
   width,height=Image.open(source_image).size
   # Chromium's native video capture needs an even raster to preserve the
   # four-pixel marker cells. Pad by at most one pixel; never rescale the PNG.
   viewport={'width':(width+1)//2*2,'height':(height+1)//2*2}
  origin='https://localhost' if tls else ORIGIN
  args=['--no-sandbox','--enable-usermedia-screen-capturing','--auto-select-tab-capture-source-by-title=Kiki complete writer fixture']
  if tls:
   public=subprocess.check_output(['openssl','x509','-pubkey','-noout','-in',str(ROOT/'work/guidance-integration/tls/cert.pem')])
   der=subprocess.check_output(['openssl','pkey','-pubin','-outform','DER'],input=public)
   args+=['--ignore-certificate-errors-spki-list='+base64.b64encode(hashlib.sha256(der).digest()).decode()]
  profile=tempfile.TemporaryDirectory(prefix='kiki-guidance-native-')
  context=await p.chromium.launch_persistent_context(profile.name,executable_path='/usr/bin/chromium',headless=True,viewport=viewport,args=args)
  browser=context
  fault={'enabled':'--invalidate-before-paint' in sys.argv,'injected':False}
  errors=[];target=await context.new_page();reader=await context.new_page();broker=await context.new_page()
  async def worker_route(route):
   req=route.request
   response=await context.request.fetch('http://127.0.0.1:8872'+req.url[len(ORIGIN):],method=req.method,headers=req.headers,data=req.post_data_buffer,timeout=30000)
   await route.fulfill(response=response)
  if not tls:await context.route(ORIGIN+'/**',worker_route)
  html=(ASSETS.parent/'scripts/fixtures/gain-dialog.html').read_text() if live_gain else '''<!doctype html><title>Kiki complete writer fixture</title><style>body{margin:0;background:#fafafa;font:18px system-ui}input{position:fixed;box-sizing:border-box;left:25vw;top:32.5vh;width:18vw;height:7vh}</style><h1>Controlled Message settings</h1><input id=frequency value="2*pi*100">'''
  if source_image:
   html='<html><head><meta charset="utf-8"><title>Kiki complete writer fixture</title><style>html,body{margin:0;width:100%;height:100%;overflow:hidden;background:white}img{display:block;width:auto;height:auto}</style></head><body><img id="source-image" src="data:image/png;base64,'+base64.b64encode(source_image.read_bytes()).decode()+'"></body></html>'
  await target.route(SOURCE,lambda r:r.fulfill(content_type='text/html',body=html))
  await broker.route('https://broker.fixture/**',lambda r:r.fulfill(body='<title>Explicit Chrome API fixture</title>'))
  await target.goto(SOURCE);await broker.goto('https://broker.fixture/')
  if high_resolution:
   # Static fine edges reproduce Simulink-like resampling; no learner pixels.
   await target.evaluate('''()=>{const canvas=document.createElement('canvas');canvas.width=innerWidth;canvas.height=innerHeight;canvas.style.cssText='position:fixed;inset:0;z-index:0;pointer-events:none';document.body.prepend(canvas);const c=canvas.getContext('2d');c.fillStyle='white';c.fillRect(0,0,innerWidth,innerHeight);c.fillStyle='#333';c.font='14px Arial';for(let y=32;y<innerHeight;y+=29){c.fillText('Message  Carrier  Modulator  Receiver  Recovery Gain 2  Frequency (rad/sec) 2*pi*2000',70,y);c.strokeStyle='#333';c.strokeRect(65,y+3,540,21);c.beginPath();c.moveTo(605,y+11);c.lineTo(innerWidth-100,y+11);c.stroke();}document.querySelector('input').style.zIndex=1;}''')
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
    if source_image and switch_image:await target.locator('#source-image').evaluate('(el,src)=>el.src=src','data:image/png;base64,'+base64.b64encode(switch_image.read_bytes()).decode())
    else:await target.locator('#frequency').evaluate("el=>el.style.left='45vw'")
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
   if tls and not live_gain:
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
   if '--expect-content-rejection' in sys.argv:
    await reader.wait_for_function("KikiWriting.diagnostics.events.some(e=>e.stage==='delivery_rejected'&&e.reason.includes('Live content differs'))",timeout=45000)
    await reader.wait_for_timeout(250)
    diag=await reader.evaluate('KikiWriting.diagnostics');assert diag['health']['painted']==0,diag
    evidence=await (await context.request.get('http://127.0.0.1:8872/__fixture/evidence')).json()
    assert any(a['status']=='rejected' and 'Live content differs' in a.get('reason','') for a in evidence['acks']),evidence
    out=ROOT/'work/still-frame-diagnostic/native-before';out.mkdir(parents=True,exist_ok=True)
    report={'status':'PASS','expected_fault':'unchanged_high_resolution_source_rejected_by_mixed_raster_comparison','source_is_static':True,'viewport':viewport,'consumer':diag}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');(out/'worker-evidence.json').write_text(json.dumps(evidence,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='consumer'},indent=2));return
   if fault['enabled']:
    await reader.wait_for_function("KikiWriting.diagnostics.events.some(e=>e.stage==='delivery_rejected')",timeout=45000)
    await reader.wait_for_timeout(150)
    diag=await reader.evaluate('KikiWriting.diagnostics')
    assert fault['injected'] and diag['health']['painted']==0,diag
    evidence=await (await context.request.get('http://127.0.0.1:8872/__fixture/evidence')).json()
    assert any(a['status']=='rejected' for a in evidence['acks']),evidence
    out=custom_out or ROOT/'work/guidance-integration/native-negative';out.mkdir(parents=True,exist_ok=True)
    report={'status':'PASS','fault':'view_invalidated_between_verification_and_paint','no_paint_ack':True,'reject_ack_persisted':True,'consumer':diag}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');(out/'worker-evidence.json').write_text(json.dumps(evidence,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='consumer'},indent=2));return
   await reader.wait_for_function("KikiWriting.diagnostics.health.painted>0||KikiWriting.diagnostics.health.analysis==='Waiting for provider'",timeout=45000)
   assert await reader.evaluate('KikiWriting.diagnostics.health.painted>0'),'Analysis did not produce a paintable drawing; inspect retained model/Worker failure'
   readable='--check-readable' in sys.argv
   if readable:await reader.wait_for_timeout(1500)
   diag=await reader.evaluate('KikiWriting.diagnostics')
   cdp=await context.new_cdp_session(target);png=base64.b64decode((await cdp.send('Page.captureScreenshot',{'format':'png'}))['data'])
   out=custom_out or ROOT/'work/guidance-integration/native';out.mkdir(parents=True,exist_ok=True);(out/'pipeline-painted.png').write_bytes(png)
   from PIL import Image
   import io
   image=Image.open(io.BytesIO(png))
   if expect_text_only:x,y=18,viewport['height']-52
   else:
    box=expected_region or await target.locator('#gain' if live_gain else '#frequency').bounding_box();x=round(box['x']+box['width']/2);y=round(box['y'])
   pixels=[image.getpixel((x+dx,y+dy))[:3] for dx in range(-4,5) for dy in range(-8,9)]
   roi=None
   if source_image and expected_region:
    roi=(max(0,int(expected_region['x'])-8),max(0,int(expected_region['y'])-8),min(image.width,int(expected_region['x']+expected_region['width'])+8),min(image.height,int(expected_region['y']+expected_region['height'])+96))
    def new_ink(actual,baseline):
     n=0
     for yy in range(roi[1],roi[3]):
      for xx in range(roi[0],roi[2]):
       r,g,b=actual.getpixel((xx,yy))[:3];old=baseline.getpixel((xx,yy))[:3]
       if b>200 and r<100 and g<170 and b>r+100 and sum(abs(a-c) for a,c in zip((r,g,b),old))>80:n+=1
     return n
    visible_ink=new_ink(image,Image.open(source_image));assert visible_ink>=8,{'new_blue_pixels_in_independent_target_roi':visible_ink}
   else:assert any(b>160 and b>r+80 for r,g,b in pixels),pixels
   await reader.wait_for_function("KikiWriting.diagnostics.events.some(e=>e.stage==='ack_recorded')",timeout=4000)
   diag=await reader.evaluate('KikiWriting.diagnostics');logs=await broker_call({'type':'diagnostics'},{'url':'chrome-extension://fixture/popup.html'})
   assert diag['painted_is_cumulative'] is True
   assert diag['current_cue'] and diag['current_cue']['operation_count']>0,diag
   requested=next(e for e in reversed(diag['events']) if e['stage']=='paint_requested')
   assert requested['marks'] and requested['ttl_ms']>0 and requested['source_ticket_age_ms']>=0,requested
   assert any(e['stage']=='paint_acknowledged' and e.get('operation_count',0)>0 and e.get('remaining_ms',0)>0 for e in diag['events']),diag
   assert any(e['stage']=='guidance_painted' for e in logs['events']),logs
   assert diag['health']['captured']>=(1 if live_gain else 2),diag
   assert not errors,errors
   evidence=await (await context.request.get('http://127.0.0.1:8872/__fixture/evidence')).json()
   (out/'worker-evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
   assert any(a['status']==('text_only' if expect_text_only else 'live_rendered') for a in evidence['acks']),evidence
   drawing=next(v for v in evidence['packets'] if v.get('message_type')=='committed_guidance')
   assert drawing['outcome']==('text_only' if expect_text_only else 'annotate'),drawing
   if source_image and expected_region:
    actual=drawing['packet']['resolved_targets'][0]['region'];expected={k:expected_region[k]/viewport['width' if k in ['x','width'] else 'height'] for k in ['x','y','width','height']}
    intersection=max(0,min(actual['x']+actual['width'],expected['x']+expected['width'])-max(actual['x'],expected['x']))*max(0,min(actual['y']+actual['height'],expected['y']+expected['height'])-max(actual['y'],expected['y']))
    overlap=intersection/(actual['width']*actual['height']+expected['width']*expected['height']-intersection)
   else:overlap=None
   switched=False
   if switch_image:
    await target.locator('#source-image').evaluate('(el,src)=>el.src=src','data:image/png;base64,'+base64.b64encode(switch_image.read_bytes()).decode())
    await reader.wait_for_function("KikiWriting.diagnostics.events.some(e=>e.stage==='invalidated'&&e.reason==='Shared view changed')",timeout=5000)
    await reader.wait_for_timeout(100)
    png_after=base64.b64decode((await cdp.send('Page.captureScreenshot',{'format':'png'}))['data']);(out/'after-switch.png').write_bytes(png_after)
    if expected_region:
     after=Image.open(io.BytesIO(png_after));assert new_ink(after,Image.open(switch_image))==0,'Old target ink survived the image view change'
    switched=True
    diag=await reader.evaluate('KikiWriting.diagnostics')
    evidence=await (await context.request.get('http://127.0.0.1:8872/__fixture/evidence')).json();(out/'worker-evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
   if live_gain:assert evidence['live_model_requests']==1,evidence
   assert await reader.evaluate('document.querySelector("#preview").srcObject.getVideoTracks()[0].getCaptureHandle()!==null')
   report={'status':'PASS','native_screen_capture':True,'real_browser_sse_stream':tls,'controller_origin_is_local_fixture_override':tls,'coherent_panel_during_stream':streamed_panel,'reader_visibility_at_paint':await reader.evaluate('document.visibilityState'),'actual_reader_worker_broker_consumer_compositor':True,'blue_pixels_at_authored_control':True,'visible_after_1500ms':readable,'persisted_exposure_ack':True,'periodic_frames_during_delayed_analysis':diag['health']['captured'],'installed_extension_tested':False,'real_simulink_tested':False,'real_model_localization_tested':live_gain,'live_model_requests':evidence['live_model_requests'],'explicit_control_setup_fixture':live_gain,'viewport':viewport,'consumer':diag}
   report.update(source_kind='user_matlab_screenshot_replay' if source_image else 'controlled_fixture',source_image_sha256=hashlib.sha256(source_image.read_bytes()).hexdigest() if source_image else None,current_outcome=drawing['outcome'],target_iou=overlap,localization_pass=overlap is None or overlap>=.5,view_switch_clears_old_ink=switched)
   if overlap is not None and overlap<.5:report['status']='FAIL_LOCALIZATION'
   (out/'pipeline-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='consumer'},indent=2))
   if overlap is not None:assert overlap>=.5,{'actual':actual,'expected':expected,'iou':overlap}
  except:
   print('CONSUMER',await reader.evaluate('KikiWriting.diagnostics'),flush=True)
   print('BROKER',await broker_call({'type':'diagnostics'},{'url':'chrome-extension://fixture/popup.html'}),flush=True)
   print('LAB',await reader.locator('#lab-status').text_content(),flush=True)
   raise
  finally:await browser.close();profile.cleanup()
asyncio.run(main())
