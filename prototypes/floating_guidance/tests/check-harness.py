"""L1: Kiki windows over a controlled underlay with real mouse/keyboard input.

No extension, server or model. Screenshots and a JSON report go to
work/floating-guidance/harness/. Run: python prototypes/floating_guidance/tests/check-harness.py
"""
import asyncio, json, sys
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parents[1] / 'work' / 'floating-guidance' / 'harness'
URL = (ROOT / 'harness' / 'index.html').as_uri()
Q = "(sel)=>{const n=__kiki.shadow.querySelector(sel);return n?{text:n.textContent.trim(),hidden:n.hidden||!n.isConnected||n.closest('[hidden]')!==null,disabled:!!n.disabled}:null}"
RECT = "(sel)=>{const r=__kiki.shadow.querySelector(sel).getBoundingClientRect();return {x:r.left,y:r.top,w:r.width,h:r.height}}"
results = []

def check(name, ok, detail=None):
    results.append({'check': name, 'passed': bool(ok), **({'detail': detail} if detail is not None else {})})
    print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else f'  {detail}'))

async def q(page, sel): return await page.evaluate(Q, sel)
async def rect(page, sel): return await page.evaluate(RECT, sel)
async def click(page, sel):
    r = await rect(page, sel); await page.mouse.click(r['x'] + r['w'] / 2, r['y'] + r['h'] / 2)

async def run():
    OUT.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        ctx = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await ctx.new_page(); errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        await page.goto(URL + '?canary'); await page.evaluate('localStorage.clear()'); await page.reload()
        scenarios = await page.evaluate('Object.keys(KIKI_FIXTURES)')
        for name in scenarios:
            await page.evaluate('n=>__kiki.show(n)', name)
            await page.screenshot(path=str(OUT / f'{name}.png'))
        # Content and labels per lifetime state.
        expect = {
            'fresh': ('.label', 'Current step'), 'waiting_first': ('.label', 'Saved step · not yet checked on screen'),
            'earlier': ('.screen h2 span', 'Earlier view'), 'paused': ('[data-action=pause]', 'Resume guidance'),
            'sharing_off': ('.label', 'Saved step · share this tab to continue'), 'blocked': ('.screen h2 span', 'Screen read paused'),
            'provider_wait': ('.screen h2 span', 'Screen reading is waiting'), 'completed': ('.now', 'Experiment complete. Review and export your journal in the tracker.'),
        }
        for name, (sel, text) in expect.items():
            await page.evaluate('n=>__kiki.show(n)', name); got = await q(page, sel)
            check(f'{name}: {sel} reads "{text}"', got and got['text'] == text, got)
        for name in scenarios:
            await page.evaluate('n=>__kiki.show(n)', name)
            now = await q(page, '.now'); want = await page.evaluate('n=>KIKI_FIXTURES[n].body.instructions.now?.title??null', name)
            if want: check(f'{name}: Now equals tracker text', now['text'] == want, [now['text'], want])
        await page.evaluate("__kiki.show('provider_wait')")
        check('provider wait keeps instructions and shows retry', 'retries in 15 min' in (await q(page, '.status'))['text'])
        await page.evaluate("__kiki.show('gain_settings')")
        cells = await page.evaluate("[...__kiki.shadow.querySelectorAll('table td')].map(n=>n.textContent)")
        check('CP-DSB-06 shows exact Gain = 2 setting', cells == ['Gain', '2'], cells)
        await page.evaluate("__kiki.show('cross_stage_next')")
        check('cross-stage Next is tagged', not (await q(page, '.tag'))['hidden'])
        await page.evaluate("__kiki.show('completed')")
        check('completed lab disables pause', (await q(page, '[data-action=pause]'))['disabled'])
        await page.evaluate("__kiki.show('fresh')"); await page.evaluate('__kiki.age(25000)')
        check('fresh view ages into an earlier view locally', (await q(page, '.screen h2 span'))['text'] == 'Earlier view')
        await page.evaluate("__kiki.show('fresh',{connection:'lost'})")
        check('lost connection keeps step, labels it not live', (await q(page, '.label'))['text'] == 'Saved step · not live' and (await q(page, '[data-action=pause]'))['disabled'])

        # Isolation: nothing that starts inside Kiki reaches the page.
        await page.evaluate("__kiki.show('fresh')"); await page.evaluate('__page.reset()')
        await click(page, '[data-action=details]'); await click(page, '[data-action=details]')
        bar = await rect(page, '[data-drag=a]')
        await page.mouse.move(bar['x'] + 60, bar['y'] + bar['h'] / 2); await page.mouse.down()
        await page.mouse.move(bar['x'] - 140, bar['y'] + 160, steps=8); await page.mouse.up()
        body = await rect(page, '.body'); await page.mouse.move(body['x'] + 40, body['y'] + 40); await page.mouse.wheel(0, 300)
        await page.mouse.dblclick(body['x'] + 40, body['y'] + 20); await page.mouse.click(body['x'] + 40, body['y'] + 20, button='right')
        await page.keyboard.press('Tab'); await page.keyboard.press('Delete'); await page.keyboard.type('2')
        leaked = await page.evaluate('__page.total')
        check('Kiki clicks, drag, wheel, double/right click and keys reach the page 0 times', leaked == 0, await page.evaluate('__page.counts'))
        moved = await page.evaluate('__kiki.state().layout.a')
        check('header drag moves the window', abs(moved['x'] - (bar['x'] - 200)) <= 2 and abs(moved['y'] - (bar['y'] + 160 - bar['h'] / 2)) <= 2, [moved, bar])
        check('drag reports moving rects for capture redaction', any(l['moving'] and l['rects'] for l in await page.evaluate('__kiki.layouts')))
        await page.mouse.click(500, 600)
        check('clicks outside Kiki still reach the page', await page.evaluate('__page.counts.click||0') > 0)
        gain = await page.evaluate("document.getElementById('gain').getBoundingClientRect().toJSON()")
        await page.mouse.click(gain['x'] + 10, gain['y'] + 8); await page.keyboard.press('Control+A'); await page.keyboard.type('2')
        check('typing in the page still works', await page.evaluate("document.getElementById('gain').value") == '2')
        await page.reload(); await page.evaluate("__kiki.show('fresh')")
        check('window position persists across reload', await page.evaluate('__kiki.state().layout.a') == moved)

        # Split / dock, keyboard move, minimize / restore.
        await click(page, '[data-action=split]')
        split = await page.evaluate("({b:!__kiki.shadow.querySelector('[data-id=b]').hidden,inB:!!__kiki.shadow.querySelector('[data-id=b] .screen')})")
        check('split shows a separate screen-context window', split['b'] and split['inB'], split)
        await page.screenshot(path=str(OUT / 'split.png'))
        await click(page, '[data-id=b] [data-action=dock]')
        check('dock returns to one window', await page.evaluate("__kiki.shadow.querySelector('[data-id=b]').hidden"))
        await page.evaluate("__kiki.shadow.querySelector('[data-drag=a]').focus()")
        before = await page.evaluate('__kiki.state().layout.a'); [await page.keyboard.press('ArrowLeft') for _ in range(3)]
        after = await page.evaluate('__kiki.state().layout.a')
        check('arrow keys move a focused window', before['x'] - after['x'] == 48, [before, after])
        await page.keyboard.press('Escape')
        mini = await page.evaluate("({launcher:!__kiki.shadow.querySelector('.launcher').hidden,focus:__kiki.shadow.activeElement?.className})")
        check('Escape minimizes to a focused launcher', mini['launcher'] and mini['focus'] == 'launcher', mini)
        await page.keyboard.press('Enter')
        check('Enter on the launcher restores without losing content', await page.evaluate("!__kiki.shadow.querySelector('[data-id=a]').hidden") and (await q(page, '.now'))['text'])
        await page.keyboard.press('Home')
        reset = await page.evaluate('__kiki.state().layout.a')
        check('Home resets to the default corner', reset['x'] == 1280 - 344 - 16 and reset['y'] == 72, reset)

        # Pause routes a command and waits for authoritative state.
        await page.evaluate("__kiki.show('fresh')"); await click(page, '[data-action=pause]')
        p_state = await q(page, '[data-action=pause]')
        check('pause sends a command and shows Pausing… until state arrives', await page.evaluate('__kiki.commands.at(-1)') == 'pause' and p_state['text'] == 'Pausing…' and p_state['disabled'], p_state)

        # Small viewport, zoom and reduced motion.
        await page.set_viewport_size({'width': 900, 'height': 600}); await page.evaluate("__kiki.show('long_content')")
        await click(page, '[data-action=details]')
        a = await rect(page, '[data-id=a]')
        check('window stays inside a 900×600 viewport', a['x'] >= 8 and a['x'] + a['w'] <= 892 and a['y'] >= 8 and a['y'] + a['h'] <= 600, a)
        check('long details scroll inside the window', await page.evaluate("(()=>{const b=__kiki.shadow.querySelector('.body');return b.scrollHeight>b.clientHeight&&getComputedStyle(b).overflowY==='auto'})()"))
        await page.screenshot(path=str(OUT / 'small-viewport-details.png'))
        # 150% browser zoom on a 1024×700 window is a 683×467 CSS viewport at DPR 1.5.
        zctx = await browser.new_context(viewport={'width': 683, 'height': 467}, device_scale_factor=1.5)
        zpage = await zctx.new_page(); await zpage.goto(URL + '?scenario=fresh')
        z = await zpage.evaluate(RECT, '[data-id=a]')
        check('readable and clamped at 150% browser zoom', z['x'] >= 8 and z['x'] + z['w'] <= 683 - 8 and z['y'] + z['h'] <= 467, z)
        await zpage.screenshot(path=str(OUT / 'zoom-150.png'))
        rctx = await browser.new_context(viewport={'width': 1280, 'height': 800}, reduced_motion='reduce')
        rpage = await rctx.new_page(); await rpage.goto(URL)
        check('reduced motion removes transitions', await rpage.evaluate("getComputedStyle(__kiki.shadow.querySelector('.btn')).transitionDuration") in ('0s',))
        dctx = await browser.new_context(viewport={'width': 1280, 'height': 800}, color_scheme='dark')
        dpage = await dctx.new_page(); await dpage.goto(URL + '?scenario=fresh'); await dpage.screenshot(path=str(OUT / 'dark.png'))
        check('no page errors', not errors, errors)
        await browser.close()
    passed = all(r['passed'] for r in results)
    (OUT / 'report.json').write_text(json.dumps({'schema': 'floating-guidance-harness/v1', 'passed': passed, 'checks': results,
        'model_calls': 0, 'real_simulink_claim': False}, indent=2))
    print(json.dumps({'passed': passed, 'checks': len(results), 'failed': sum(not r['passed'] for r in results), 'report': str(OUT / 'report.json')}))
    return passed

if __name__ == '__main__':
    sys.exit(0 if asyncio.run(run()) else 1)
