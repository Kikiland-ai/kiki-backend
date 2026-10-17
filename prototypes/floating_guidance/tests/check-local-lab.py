"""L2: real reader + dev extension + controlled target tab, fixture provider only.

Starts serve-local-lab.mjs (reader :8870, target :8871), loads the unpacked dev
extension into Playwright Chromium, binds the target tab, shares it with native
tab capture and walks the lab-coherence scenarios from the test plan. Every
non-localhost fetch in the server throws, so no live model can be reached.
Prerequisites: node scripts/build.mjs (reader) and build-extension.mjs (dev).
Run from the repository root: python prototypes/floating_guidance/tests/check-local-lab.py
"""
import asyncio, base64, json, shutil, subprocess, sys, tempfile, time, urllib.error, urllib.request
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[3]
READER_DIR = ROOT / 'prototypes' / 'json_stream_site'
EXT = ROOT / 'work' / 'floating-guidance' / 'dev'
OUT = ROOT / 'work' / 'floating-guidance' / 'local-lab'
results, timeline = [], []
READER = None
SHADOW = "(sel)=>{const r=document.querySelector('kiki-floating-guidance')?.shadowRoot,n=r?.querySelector(sel);return n?{text:n.textContent.trim(),hidden:!!n.closest('[hidden]'),disabled:!!n.disabled}:null}"
RECT = "(sel)=>{const n=document.querySelector('kiki-floating-guidance').shadowRoot.querySelector(sel).getBoundingClientRect();return {x:n.left,y:n.top,w:n.width,h:n.height}}"
SCAN = """async(images)=>{let magenta=0,grey=0,total=0;for(const b64 of images){const bmp=await createImageBitmap(await (await fetch('data:image/jpeg;base64,'+b64)).blob());
 const c=new OffscreenCanvas(bmp.width,bmp.height),x=c.getContext('2d');x.drawImage(bmp,0,0);const d=x.getImageData(0,0,bmp.width,bmp.height).data;
 for(let i=0;i<d.length;i+=4){total++;if(d[i]>190&&d[i+1]<100&&d[i+2]>190)magenta++;if(Math.abs(d[i]-127)<8&&Math.abs(d[i+1]-127)<8&&Math.abs(d[i+2]-127)<8)grey++;}}
 return {images:images.length,magenta,grey,total}}"""

def check(name, ok, detail=None):
    results.append({'check': name, 'passed': bool(ok), **({'detail': detail} if detail is not None else {})})
    print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else f'  {json.dumps(detail, default=str)[:400]}'), flush=True)

def fixture(path='/__fixture/state', mode=None):
    data = json.dumps({'mode': mode}).encode() if mode else None
    started = time.monotonic()
    # The test client's polling socket is occasionally reset on Windows while the
    # reader streams; retry and record it so the report keeps the count visible.
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8870' + path, data=data, method='POST' if data else 'GET'), timeout=30) as r:
                value = json.loads(r.read())
            break
        except ConnectionResetError:
            timeline.append({'fixture_connection_reset': path, 'attempt': attempt + 1})
            if attempt == 2: raise
            time.sleep(0.2)
    elapsed = time.monotonic() - started
    if elapsed > 2: timeline.append({'slow_fixture_request': path, 'seconds': round(elapsed, 2)})
    return value

def model_jpegs(count=3):
    """The last model-bound JPEGs, base64-encoded for the in-browser scan."""
    images = []
    for index in range(-count, 0):
        # Same Windows socket reset as fixture(): retry, and keep the count in the report.
        for attempt in range(3):
            try:
                with urllib.request.urlopen(f'http://127.0.0.1:8870/__fixture/image?index={index}', timeout=30) as r: images.append(base64.b64encode(r.read()).decode())
                break
            except urllib.error.HTTPError: break
            except ConnectionResetError:
                timeline.append({'fixture_connection_reset': f'image {index}', 'attempt': attempt + 1})
                if attempt == 2: raise
                time.sleep(0.2)
    return images

async def model_image(pred, timeout=40):
    """Wait for a newly received model-bound image whose canary scan satisfies pred."""
    seen = (await asyncio.to_thread(fixture))['model_calls']; end = time.monotonic() + timeout; scan = None
    while time.monotonic() < end:
        state = await asyncio.to_thread(fixture)
        if state['model_calls'] > seen:
            seen = state['model_calls']; image = (await asyncio.to_thread(model_jpegs, 1))[-1]
            scan = await READER.evaluate(SCAN, [image]); scan['image'] = image
            if pred(scan): return scan
        await asyncio.sleep(0.3)
    return scan

async def until(fn, pred=bool, timeout=20, step=0.25):
    """Poll an async getter until pred(value); returns the value if it passed, else None."""
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        value = await fn()
        if pred(value): return value or True
        await asyncio.sleep(step)
    return None

async def kiki(target, sel): return await target.evaluate(SHADOW, sel)
async def kiki_click(target, sel):
    r = await target.evaluate(RECT, sel); await target.mouse.click(r['x'] + r['w'] / 2, r['y'] + r['h'] / 2)

async def coherent(reader, target):
    now = (await kiki(target, '.now') or {}).get('text'); nxt = (await kiki(target, '.next') or {}).get('text')
    r_now = (await reader.text_content('#lab-current') or '').strip(); r_next = (await reader.text_content('#lab-next') or '').strip().removeprefix('Coming next: ')
    return {'ok': bool(now) and now == r_now and nxt == r_next, 'window_now': now, 'reader_now': r_now, 'window_next': nxt, 'reader_next': r_next}

async def shot(page, name): await page.screenshot(path=str(OUT / f'{name}.png'))

async def run():
    OUT.mkdir(parents=True, exist_ok=True)
    if not (EXT / 'manifest.json').exists(): raise SystemExit('Build the dev extension first.')
    # Server output goes to a file: an undrained pipe would block the Worker's logging.
    server_log = open(OUT / 'server.log', 'w')
    server = subprocess.Popen(['node', '../floating_guidance/scripts/serve-local-lab.mjs'], cwd=READER_DIR, stdout=server_log, stderr=subprocess.STDOUT)
    profile = tempfile.mkdtemp(prefix='kiki-fg-')
    try:
        for _ in range(100):
            try: fixture(); urllib.request.urlopen('http://127.0.0.1:8871/', timeout=1); break
            except Exception: time.sleep(0.1)
        async with async_playwright() as p:
            ctx = await p.chromium.launch_persistent_context(profile, channel='chromium', headless=True, viewport={'width': 1280, 'height': 800}, args=[
                f'--disable-extensions-except={EXT}', f'--load-extension={EXT}', '--enable-usermedia-screen-capturing',
                '--allow-http-screen-capture', '--auto-select-tab-capture-source-by-title=Kiki target fixture'])
            sw = ctx.service_workers[0] if ctx.service_workers else await ctx.wait_for_event('serviceworker', timeout=10000)
            errors = []
            target = ctx.pages[0] if ctx.pages else await ctx.new_page()
            target.on('pageerror', lambda e: errors.append('target: ' + str(e)))
            await target.goto('http://localhost:8871/')
            reader = await ctx.new_page(); reader.on('pageerror', lambda e: errors.append('reader: ' + str(e)))
            await reader.goto('http://localhost:8870/')
            check('extension bridge detected on the reader', await until(lambda: reader.evaluate('window.KikiFloating?.status().present===true'), bool, 10))
            await reader.fill('#lab-model-name', 'dsb_sc_test'); await reader.click('#lab-begin')
            await reader.wait_for_function("document.getElementById('lab-current').textContent.length>0")
            bound = await sw.evaluate("async()=>{const [t]=await chrome.tabs.query({url:'http://localhost:8871/*'});return kikiTest.bind(t.id)}")
            check('target tab bound with a capture handle', bound.get('ok') and bound.get('capture_handle_set'), bound)

            # 1. Cold connect: saved instructions appear before any screen read.
            c = await until(lambda: coherent(reader, target), lambda v: v['ok'], 10) or await coherent(reader, target)
            check('cold connect shows the saved current/next step before any analysis', c and c['ok'], c)
            label = await kiki(target, '.label')
            check('cold connect labels the step as saved, sharing off', label and label['text'] == 'Saved step · share this tab to continue', label)
            check('no model call before sharing', fixture()['model_calls'] == 0)
            await shot(target, '01-cold-connect')

            # 2. Share the target tab; frames are masked, analysis runs on the fixture.
            await reader.bring_to_front(); await reader.click('#share')
            check('first screen read reaches the fixture provider', await until(lambda: asyncio.to_thread(lambda: fixture()['model_calls'] > 0), bool, 30))
            heading = await until(lambda: kiki(target, '.screen h2 span'), lambda v: v and v['text'] == 'What I can see', 20)
            check('accepted observation appears in the screen-context window', heading, await kiki(target, '.screen h2 span'))
            c = await coherent(reader, target); check('reader and window agree after the first accepted read', c['ok'], c)
            status = await reader.evaluate('KikiFloating.status()')
            check('captured frames are redacted, not blocked, when the bound tab is shared', status['frames']['redact'] > 0, status['frames'])
            scan = await reader.evaluate(SCAN, model_jpegs(3))
            check('model-bound JPEGs contain no canary pixels', scan['images'] > 0 and scan['magenta'] == 0, scan)
            check('model-bound JPEGs contain the grey Kiki mask', scan['grey'] > 1000, scan)
            png = base64.b64encode(await target.screenshot()).decode()
            visible = await reader.evaluate(SCAN.replace("'data:image/jpeg;base64,'", "'data:image/png;base64,'"), [png])
            check('the canary is visible to the learner on the tab (positive control)', visible['magenta'] > 200, visible)
            await shot(target, '02-live-fresh')
            (OUT / 'model-bound-masked.jpg').write_bytes(base64.b64decode(model_jpegs(1)[-1]))
            # Negative control: with masking switched off the same scan must find the canary.
            global READER; READER = reader
            await reader.evaluate("window.__realSafety=KikiFloating.sampleSafety;KikiFloating.sampleSafety=()=>({mode:'none'})")
            leak = await model_image(lambda v: v['magenta'] > 100)
            await reader.evaluate("KikiFloating.sampleSafety=window.__realSafety")
            if leak: (OUT / 'model-bound-unmasked-control.jpg').write_bytes(base64.b64decode(leak.pop('image')))
            check('negative control: unmasked capture does contain the canary', leak and leak['magenta'] > 100, leak)
            rescan = await model_image(lambda v: v['magenta'] == 0 and v['grey'] > 1000)
            if rescan: rescan.pop('image', None)
            check('masking resumes after the control', rescan and rescan['magenta'] == 0, rescan)

            # 3. Advance: the tracker moves on; the window follows atomically.
            before = (await kiki(target, '.now'))['text']; fixture('/__fixture/mode', 'match')
            changed = await until(lambda: kiki(target, '.now'), lambda v: v and v['text'] != before, 45)
            fixture('/__fixture/mode', 'unknown')
            check('window Now changes when the tracker advances', changed, {'before': before})
            c = await until(lambda: coherent(reader, target), lambda v: v['ok'], 6) or await coherent(reader, target)
            check('reader and window agree after the advance', c['ok'], c)

            # 4. Pause and resume from the window use the authoritative lab action.
            await kiki_click(target, '[data-action=pause]')
            paused = await until(lambda: reader.text_content('#lab-pause'), lambda t: t == 'Resume guidance', 10)
            check('window Pause pauses the lab in the tracker', paused)
            wl = await until(lambda: kiki(target, '.label'), lambda v: v and v['text'] == 'Guidance paused', 8)
            check('window shows the paused state from the authoritative snapshot', wl, await kiki(target, '.label'))
            await shot(target, '03-paused')
            await kiki_click(target, '[data-action=pause]')
            check('window Resume resumes the lab', await until(lambda: reader.text_content('#lab-pause'), lambda t: t == 'Pause guidance', 10))

            # 5. Interacting with Kiki never reaches the page or mutates the lab.
            lab_id = await reader.evaluate("localStorage.getItem('kiki-last-lab-id')")
            events = await reader.evaluate("id=>fetch(`/lab-sessions/${id}/events?after=0&limit=100`).then(r=>r.json())", lab_id)
            last_seq = events[-1]['event_sequence'] if len(events) < 100 else None
            await target.evaluate('__page.reset()')
            await kiki_click(target, '[data-action=details]'); await kiki_click(target, '[data-action=details]')
            bar = await target.evaluate(RECT, '[data-drag=a]')
            await target.mouse.move(bar['x'] + 60, bar['y'] + 20); await target.mouse.down(); await target.mouse.move(bar['x'] - 200, bar['y'] + 120, steps=10); await target.mouse.up()
            await target.keyboard.press('Tab'); await target.keyboard.press('Delete')
            check('Kiki interactions reach the page 0 times', await target.evaluate('__page.total') == 0, await target.evaluate('__page.counts'))
            await asyncio.sleep(1.5)
            if last_seq is not None:
                later = await reader.evaluate("([id,a])=>fetch(`/lab-sessions/${id}/events?after=${a}&limit=100`).then(r=>r.json())", [lab_id, last_seq])
                student = [e['event_type'] for e in later if not e['event_type'].startswith('analysis_')]
                check('window drag/details/keys create no lab events', not student, student)
            timeline.append({'after_drag_frames': (await reader.evaluate('KikiFloating.status()'))['frames']})

            # 6. Lifecycle: target reload, worker restart, stop sharing, reader close.
            await target.reload()
            back = await until(lambda: coherent(reader, target), lambda v: v['ok'], 15)
            check('after a MATLAB-tab reload the windows return with fresh content', back, await coherent(reader, target))
            r0 = (await reader.evaluate('KikiFloating.status()'))['frames']['redact']
            check('capture handle restored after reload (frames redact again)', await until(lambda: reader.evaluate('KikiFloating.status().frames.redact'), lambda n: n > r0, 15))
            restarted = None
            try:
                cdp = await ctx.new_cdp_session(reader)
                targets = (await cdp.send('Target.getTargets'))['targetInfos']
                worker = next(t for t in targets if t['type'] == 'service_worker' and t['url'].endswith('/background.js'))
                await cdp.send('Target.closeTarget', {'targetId': worker['targetId']}); restarted = True
            except Exception as e:
                restarted = str(e)
            seq0 = (await reader.evaluate('KikiFloating.status()'))['sequence']
            alive = await until(lambda: reader.evaluate('KikiFloating.status()'), lambda s: s['sequence'] > seq0 + 1 and (s['display'] or {}).get('result') in ('displayed', 'duplicate'), 15)
            check('snapshots keep displaying after the extension worker stops', restarted is True and alive, {'restart': restarted, 'status': alive})
            fixture('/__fixture/mode', '429')
            waiting = await until(lambda: kiki(target, '.status'), lambda v: v and 'retries' in v['text'], 25)
            check('provider wait keeps the step and shows the retry', waiting and (await kiki(target, '.now'))['text'], await kiki(target, '.status'))
            await shot(target, '04-provider-wait')
            fixture('/__fixture/mode', 'unknown')
            await reader.bring_to_front(); await reader.click('#stop')
            off = await until(lambda: kiki(target, '.label'), lambda v: v and v['text'] == 'Saved step · share this tab to continue', 10)
            check('stop sharing keeps the saved step and says sharing is off', off, await kiki(target, '.label'))
            diagnostics = await reader.evaluate('KikiFloating.diagnostics()')
            await reader.close()
            gone = await until(lambda: kiki(target, '.status'), lambda v: v and v['text'] == 'Not connected to the Kiki tracker', 10)
            check('closing the tracker leaves an explicit not-connected window', gone, await kiki(target, '.status'))
            check('saved step stays readable after the tracker closes', (await kiki(target, '.label'))['text'] == 'Saved step · not live')
            await shot(target, '05-tracker-closed')
            stats = fixture()
            check('zero live network requests were attempted', stats['blocked_network_requests'] == 0, stats)
            check('no page errors', not errors, errors)
            await ctx.close()
    finally:
        server.terminate(); server_log.close(); shutil.rmtree(profile, ignore_errors=True)
    passed = all(r['passed'] for r in results)
    (OUT / 'report.json').write_text(json.dumps({'schema': 'floating-guidance-local-lab/v1', 'passed': passed, 'checks': results,
        'fixture': stats, 'timeline': timeline, 'reader_events': diagnostics['events'][-80:], 'model': 'local fixture only', 'real_simulink_claim': False}, indent=2, default=str))
    print(json.dumps({'passed': passed, 'checks': len(results), 'failed': sum(not r['passed'] for r in results), 'report': str(OUT / 'report.json')}))
    return passed

if __name__ == '__main__':
    sys.exit(0 if asyncio.run(run()) else 1)
