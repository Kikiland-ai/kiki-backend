"""Controlled native tab-share QA. Requires an explicitly injected fixture analyzer."""

import argparse
import asyncio
import json
import shutil
from pathlib import Path

from playwright.async_api import async_playwright


async def check(args):
    args.output_dir.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=args.chromium or shutil.which('chromium'), headless=True,
            args=['--no-sandbox', '--enable-usermedia-screen-capturing', '--allow-http-screen-capture',
                  '--auto-select-tab-capture-source-by-title=Kiki controlled lab target'])
        try:
            context = await browser.new_context(viewport={'width': 1280, 'height': 1000})
            target = await context.new_page()
            await target.goto(args.url)
            await target.evaluate("""() => {
                document.title='Kiki controlled lab target';
                document.body.innerHTML='<main><h1>CONTROLLED LAB FIXTURE</h1><p>Model: dsb_sc_fixture</p><p>Message → Product ← Carrier</p></main>';
            }""")
            page = await context.new_page()
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            await page.goto(args.url)
            health = await page.evaluate("fetch('/health').then(r=>r.json())")
            assert health['analysis']['model'] == 'controlled_fixture_no_provider', 'Do not run fixture UI QA against a live model adapter'
            await page.locator('#lab-model-name').fill('dsb_sc_fixture')
            await page.locator('#lab-operator').check()
            await page.locator('#lab-begin').click()
            await page.wait_for_function("!document.getElementById('lab-run').hidden")
            lab_id = await page.evaluate("localStorage.getItem('kiki-python-lab-id')")
            await page.locator('#share').click()
            await page.wait_for_function("Number(document.getElementById('count').textContent)>=2", timeout=20000)
            await page.wait_for_function("!document.getElementById('lab-check').disabled")
            await page.locator('#lab-check').click()
            await page.wait_for_function("document.getElementById('lab-checked').naturalWidth>0 && !document.getElementById('lab-review').disabled", timeout=15000)
            for item in await page.locator('#lab-criteria input').all():
                await item.check()
            await page.locator('#lab-review-note').fill('Controlled fixture review for transport and checkpoint UI acceptance.')
            await page.locator('#lab-review').click()
            await page.wait_for_function("document.getElementById('lab-current').textContent.includes('Message and Carrier')")
            await page.locator('#lab-response-kind').select_option('question')
            await page.locator('#lab-response-text').fill('Controlled question: why does a time-based source use radians per second?')
            await page.locator('#lab-save-response').click()
            await page.wait_for_function("document.getElementById('lab-status').textContent.includes('Student report saved')")
            await page.locator('#stop').click()
            await page.wait_for_function("!document.getElementById('share').disabled")
            await page.reload()
            await page.wait_for_function("document.getElementById('lab-current').textContent.includes('Message and Carrier')")
            await page.locator('#share').click()
            await page.wait_for_function("Number(document.getElementById('count').textContent)>=2", timeout=20000)
            state = await page.evaluate("id=>fetch('/lab-sessions/'+id).then(r=>r.json())", lab_id)
            assert state['workspace']['capture_epoch'] == 2
            assert state['queue']['done_checkpoint_ids'] == ['CP-DSB-01']
            assert state['responses'][0]['kind'] == 'question'
            assert state['responses'][0]['interpretation'] == 'student_report_unassessed'
            assert state['runtime']['analysis_attempts'] == 1
            await page.screenshot(path=str(args.output_dir/'python-lab.png'), full_page=True)
            await page.locator('#stop').click()
            await page.wait_for_function("!document.getElementById('share').disabled")
            assert not errors, errors
            report = {'status': 'PASS', 'backend': 'python_fastapi', 'source': 'controlled_fixture_tab',
                      'analysis': 'explicit_injected_fixture', 'native_getDisplayMedia': True,
                      'checked_pixels_visible': True, 'reviewed_advancement': True, 'response_journal': True,
                      'reload_reconnect_preserves_queue': True, 'javascript_errors': errors,
                      'real_simulink_recognition': False, 'live_overlay_acceptance': False}
            (args.output_dir/'report.json').write_text(json.dumps(report, indent=2)+'\n')
            print(json.dumps(report, indent=2))
        finally:
            await browser.close()


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--url', default='http://127.0.0.1:8766')
parser.add_argument('--chromium')
parser.add_argument('--output-dir', type=Path, default=Path('work/python-lab-browser'))
asyncio.run(check(parser.parse_args()))
