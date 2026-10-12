#!/usr/bin/env node
/*
 * Seeds known errors into copies of the v2 ledgers and checks that validate.js reports each one.
 * Usage: node tools/test-validator.js
 */
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');

const root = path.join(__dirname, '..');
const load = (p) => JSON.parse(fs.readFileSync(path.join(root, 'ledgers', p), 'utf8'));
const DIODE = 'electronics/diodes-and-rectifiers.json', CHEM = 'chemical/steady-state-material-balances.json', MATH = 'mathematics/eigenvalues-from-a-question.json';
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'ledger-test-'));

const cases = [
  { name: 'chapter scope with one broad concept', rule: 'P1', base: MATH, mutate: (L) => { L.lessonPlan.scope = 'chapter'; } },
  { name: 'lab check in a subject without practicals', rule: 'C4', base: MATH, mutate: (L) => { L.concepts[0].checks.push({ ...L.concepts[0].checks[0], id: 'Q-x', dimension: 'lab' }); } },
  { name: 'practical linked in a subject without practicals', rule: 'T2', base: MATH, mutate: (L) => { L.concepts[0].practicalId = 'PR-X'; } },
  { name: 'exam signal disagrees with past papers', rule: 'X2', base: CHEM, mutate: (L) => { L.concepts[0].examSignal.askedIn = 2; } },
  { name: 'interactive formula uses an unknown name', rule: 'C1', base: CHEM, mutate: (L) => { L.concepts[0].explanation.modalities.interactive.outputs[0].formula = 'F1+F3'; } },
  { name: 'no syllabus lines and no request', rule: 'CE2', base: MATH, mutate: (L) => { delete L.lessonPlan.requestId; } },
  { name: 'term introduced twice', rule: 'ME2', base: DIODE, mutate: (L) => { L.concepts[1].termIds.push(L.concepts[0].termIds[0]); } },
  { name: 'walkthrough target not in text', rule: 'C1', base: DIODE, mutate: (L) => { L.concepts[0].explanation.modalities.voice.walkthrough[0].target = 'not in the text'; } },
  { name: 'worked rubric does not add up', rule: 'C3', base: CHEM, mutate: (L) => { L.concepts[1].workedQuestion.rubric[0].marks = 3; } },
  { name: 'prerequisite cycle', rule: 'D2', base: DIODE, mutate: (L) => { L.concepts[0].prerequisiteIds.push('C-1.3'); } },
  { name: 'missing words check', rule: 'C4', base: MATH, mutate: (L) => { L.concepts[0].checks = L.concepts[0].checks.filter((q) => q.dimension !== 'words'); } },
  { name: 'same term owned in two ledgers of one course', rule: 'XL1', base: CHEM, pair: true, mutate: (L) => { L.lessonPlan.id = 'LP-MB2'; L.course.lessonPlanIds = ['LP-MB2']; L.concepts.forEach((c) => { c.id += 'b'; c.canonicalKey += '-b'; }); /* ids changed but terms keep their names */ L.terms.forEach((t) => { t.id += 'b'; t.ownerConceptId += 'b'; }); L.concepts.forEach((c) => { c.termIds = c.termIds.map((x) => x + 'b'); c.usesTermIds = c.usesTermIds.map((x) => x + 'b'); c.prerequisiteIds = c.prerequisiteIds.map((x) => x + 'b'); }); L.broadConcepts.forEach((b) => { b.lessonPlanId = 'LP-MB2'; b.conceptIds = b.conceptIds.map((x) => x + 'b'); }); } },
  { name: 'term used but introduced nowhere in the course', rule: 'XL2', base: MATH, pair: true, mutate: (L) => { L.concepts[0].usesTermIds.push('T-nowhere'); } }
];

let failed = 0;
cases.forEach((tc, i) => {
  const L = load(tc.base);
  tc.mutate(L);
  const f = path.join(tmp, `case-${i}.json`);
  fs.writeFileSync(f, JSON.stringify(L));
  const files = [f];
  if (tc.pair) files.push(path.join(root, 'ledgers', tc.base));
  const r = spawnSync(process.execPath, [path.join(root, 'validate.js'), ...files], { encoding: 'utf8' });
  const caught = r.status === 1 && r.stdout.includes(`ERROR [${tc.rule}]`);
  if (!caught) failed++;
  console.log(`${caught ? 'caught ' : 'MISSED '} ${tc.rule.padEnd(4)} ${tc.name}`);
});
fs.rmSync(tmp, { recursive: true, force: true });
console.log(failed ? `\n${failed} seeded error(s) missed.` : `\nAll ${cases.length} seeded errors caught.`);
process.exit(failed ? 1 : 0);
