"""Native fixture tab capture with an explicitly mocked slow/failing vision provider.
Run the local dev server with --analysis-fixture. This checks UI isolation, not model accuracy.
"""
import asyncio,json,shutil
from pathlib import Path
from playwright.async_api import async_playwright

async def check():
    output=Path('work/analysis-browser-check');output.mkdir(parents=True,exist_ok=True)
    async with async_playwright() as p:
        browser=await p.chromium.launch(executable_path=shutil.which('chromium'),headless=True,args=[
            '--no-sandbox','--enable-usermedia-screen-capturing','--allow-http-screen-capture',
            '--auto-select-tab-capture-source-by-title=Kiki analysis fixture'])
        try:
            context=await browser.new_context(viewport={'width':1280,'height':1100})
            target=await context.new_page();await target.goto('http://localhost:8870')
            await target.evaluate("""() => {
              document.title='Kiki analysis fixture';
              document.body.innerHTML='<main><h1>Oscillator controls</h1><p>Status: Paused</p><p>Control voltage: -0.5 V</p><p>Output frequency: 950 Hz</p><button>Run</button></main>';
            }""")
            page=await context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            await page.goto('http://localhost:8870');await page.locator('#share').click()
            await page.wait_for_function("Number(document.getElementById('count').textContent)>=2",timeout=15000)
            assert 'ANALYZING FRAME' in await page.locator('#analysis-state').inner_text(), 'Slow analysis did not overlap capture'
            await page.wait_for_function("document.getElementById('analysis-facts').children.length===2",timeout=15000)
            first=json.loads(await page.locator('#json').inner_text())
            assert first['observation']['source_frame']['sequence']==1
            assert first['observation']['latest_frame']['sequence']>1,'Late result regressed newest frame'
            assert first['received_frame_count']>=2
            await page.wait_for_function("JSON.parse(document.getElementById('json').textContent).analysis.status==='failed'",timeout=18000)
            failure=json.loads(await page.locator('#json').inner_text());count=failure['received_frame_count']
            assert failure['analysis']['error']=='provider_http_503'
            assert failure['observation']['summary']==first['observation']['summary']
            await page.wait_for_function("n=>Number(document.getElementById('count').textContent)>n",arg=count,timeout=6000)
            assert await page.evaluate("document.getElementById('preview').srcObject.getVideoTracks()[0].readyState==='live'")
            await page.screenshot(path=str(output/'analysis.png'),full_page=True)
            await page.locator('#pause').click()
            await page.wait_for_function("JSON.parse(document.getElementById('json').textContent).capture_status==='paused'")
            count=int(await page.locator('#count').inner_text());await page.wait_for_timeout(2300)
            assert int(await page.locator('#count').inner_text())==count
            await page.locator('#pause').click()
            await page.wait_for_function("n=>Number(document.getElementById('count').textContent)>n",arg=count,timeout=6000)
            await page.locator('#stop').click()
            await page.wait_for_function("JSON.parse(document.getElementById('json').textContent).capture_status==='ended'")
            assert not errors,errors
            report={'status':'PASS','native_getDisplayMedia':True,'provider':'explicit_local_mock',
              'slow_analysis_does_not_block_uploads':True,'late_analysis_preserves_latest_frame':True,
              'provider_503_does_not_stop_capture':True,'previous_observation_preserved_on_failure':True,
              'pause_resume_stop':True,'received_frames':int(await page.locator('#count').inner_text()),'javascript_errors':errors}
            (output/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
        finally: await browser.close()
asyncio.run(check())
