"""Native Chromium tab-capture smoke test against an already running receiver.

The automatically selected source is a controlled fixture tab, not the user's desktop.
Requires Playwright and Chromium; writes only ignored work/ evidence by default.
"""

import argparse
import asyncio
import json
import shutil
from pathlib import Path

from playwright.async_api import async_playwright


async def check(args):
    args.output_dir.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        chromium = args.chromium or shutil.which("chromium")
        browser = await p.chromium.launch(executable_path=chromium, headless=True, args=[
            "--no-sandbox", "--enable-usermedia-screen-capturing", "--allow-http-screen-capture",
            "--auto-select-tab-capture-source-by-title=Kiki capture test target",
        ])
        try:
            context = await browser.new_context(viewport={"width": 1280, "height": 900})
            target = await context.new_page()
            await target.goto(args.url)
            await target.evaluate("""() => {
                document.title = 'Kiki capture test target';
                document.body.innerHTML = '<main><h1>FRAME RECEIVER TEST</h1><p id="value">Control voltage: 0.5 V</p></main>';
            }""")
            page = await context.new_page()
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            await page.goto(args.url)
            await page.locator("#share").click()
            await page.wait_for_function("Number(document.getElementById('count').textContent) >= 2", timeout=20000)
            await page.wait_for_function("document.getElementById('remote').naturalWidth > 0")
            before = json.loads(await page.locator("#json").inner_text())
            before_hash = before["observation"]["latest_frame"]["sha256"]
            await target.locator("#value").evaluate("el => el.textContent = 'Control voltage: 1.0 V'")
            await page.wait_for_function("""previous => {
                const data = JSON.parse(document.getElementById('json').textContent);
                return data.observation.latest_frame.sha256 !== previous;
            }""", arg=before_hash, timeout=8000)
            await page.wait_for_timeout(300)
            await page.screenshot(path=str(args.output_dir / "receiver.png"), full_page=True)
            await page.locator("#pause").click()
            await page.wait_for_function("JSON.parse(document.getElementById('json').textContent).capture_status === 'paused'")
            paused_count = int(await page.locator("#count").inner_text())
            await page.wait_for_timeout(2500)
            assert int(await page.locator("#count").inner_text()) == paused_count, "Pause allowed new frames"
            await page.locator("#pause").click()
            await page.wait_for_function("n => Number(document.getElementById('count').textContent) > n", arg=paused_count, timeout=8000)
            await page.locator("#stop").click()
            await page.wait_for_function("!document.getElementById('share').disabled")
            final = json.loads(await page.locator("#json").inner_text())
            assert final["capture_status"] == "ended"
            assert not final["evidence"]["latest_image_available"]
            assert not errors, errors
            report = {"status": "PASS", "source": "controlled_fixture_tab",
                      "native_getDisplayMedia": True, "actual_server_returned_image": True,
                      "visible_source_change_updates_hash": True, "pause_resume_stop": True,
                      "received_frames": final["received_frame_count"], "javascript_errors": errors,
                      "model_analysis": "not_enabled"}
            (args.output_dir / "browser-check.json").write_text(json.dumps(report, indent=2) + "\n")
            print(json.dumps(report, indent=2))
        finally:
            await browser.close()


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--url", default="http://127.0.0.1:8765")
parser.add_argument("--chromium")
parser.add_argument("--output-dir", type=Path, default=Path("work/screen-capture-browser-check"))
asyncio.run(check(parser.parse_args()))
