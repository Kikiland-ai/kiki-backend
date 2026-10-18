// Real extension renderer/core under a DOM boundary; no student/provider state.
// KIKI_WEB_CHECKOUT points to the web checkout supplying its locked jsdom dependency.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { resolve } from 'node:path';
import vm from 'node:vm';
const require = createRequire(import.meta.url);
const { JSDOM } = require(resolve(process.env.KIKI_WEB_CHECKOUT, 'apps/web/node_modules/jsdom/lib/api.js'));
const sources = await Promise.all(['core', 'ui'].map(name => readFile(new URL(`../extension/${name}.js`, import.meta.url), 'utf8')));
function setup() {
  const dom = new JSDOM('<!doctype html><body></body>', { runScripts: 'outside-only', pretendToBeVisual: true });
  const win = dom.window;
  win.ResizeObserver = class { observe() {} };
  for (const source of sources) vm.runInContext(source, dom.getInternalVMContext());
  const host = win.document.createElement('div'); win.document.body.append(host);
  const shadow = host.attachShadow({ mode: 'open' }), commands = [];
  const ui = win.KikiFloatingUI.create({ host, shadow, onCommand: command => commands.push(command) });
  const model = (checkpoint, connection = 'live', status = 'active') => win.KikiFloatingCore.viewModel({ body: {
    lab: { status }, instructions: { now: { checkpoint_id: checkpoint, title: 'Save and review your model', how: [], settings: [] }, next: null },
    runtime: { capture_active: true, reading: false, retry_after_ms: null },
    screen_context: { status: 'fresh', age_ms: 0, fresh_for_ms: 20000, check: [], uncertainties: [] },
  } }, { connection });
  const click = () => { shadow.querySelector('[data-action="focus_confirmation"]').focus(); ui.handleEvent({ type: 'click', detail: 0 }); };
  return { dom, shadow, ui, model, commands, click };
}
for (const checkpoint of ['CP-DSB-01', 'CP-DSB-12']) test(`${checkpoint}: confirmation beside Now opens the reader and explicitly cannot save MATLAB`, () => {
  const t = setup();
  try {
    t.ui.render(t.model(checkpoint));
    const button = t.shadow.querySelector('[data-action="focus_confirmation"]');
    assert.equal(button.hidden, false); assert.equal(button.disabled, false);
    assert.equal(button.closest('.guide') !== null, true);
    assert.match(button.nextElementSibling.textContent, /does not save the model/);
    assert.match(button.nextElementSibling.textContent, /Save the model in MATLAB first/);
    t.click(); assert.deepEqual(t.commands, ['focus_confirmation']);
  } finally { t.dom.window.close(); }
});
test('other steps, empty, disconnected, takeover, and completed states cannot trigger the saved-model control', () => {
  const t = setup();
  try {
    t.ui.render(t.model('CP-DSB-02')); t.click();
    assert.equal(t.shadow.querySelector('[data-action="focus_confirmation"]').hidden, true);
    for (const connection of ['disconnected', 'superseded', 'reconnecting']) { t.ui.render(t.model('CP-DSB-01', connection)); t.click(); }
    t.ui.render(t.model('CP-DSB-12', 'live', 'completed')); t.click();
    t.ui.render(t.dom.window.KikiFloatingCore.viewModel(null)); t.click();
    assert.equal(t.shadow.querySelector('[data-action="focus_confirmation"]').hidden, true);
    assert.deepEqual(t.commands, []);
  } finally { t.dom.window.close(); }
});
