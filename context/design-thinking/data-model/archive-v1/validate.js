#!/usr/bin/env node
/*
 * Validates a lesson-plan ledger against the MECE pyramid rules.
 * Usage: node validate.js diodes-and-rectifiers.ledger.json
 * Exit code 0 = valid, 1 = errors. Warnings never fail the run.
 */
const fs = require('fs');
const file = process.argv[2] || 'diodes-and-rectifiers.ledger.json';
const L = JSON.parse(fs.readFileSync(file, 'utf8'));
const errors = [], warnings = [];
const err = (rule, msg) => errors.push(`[${rule}] ${msg}`);
const warn = (rule, msg) => warnings.push(`[${rule}] ${msg}`);

const lp = L.lessonPlan;
const bcs = L.broadConcepts, cs = L.concepts, objs = L.objectives, terms = L.terms;
const byId = (arr) => Object.fromEntries(arr.map((x) => [x.id, x]));
const BC = byId(bcs), C = byId(cs), O = byId(objs), T = byId(terms);

// ---------- Pyramid structure ----------
if (lp.broadConceptIds.length < 2 || lp.broadConceptIds.length > 5) err('P1', `Lesson plan should split into 2 to 5 broad concepts (has ${lp.broadConceptIds.length}).`);
lp.broadConceptIds.forEach((id) => { if (!BC[id]) err('P2', `Broad concept ${id} listed on the lesson plan does not exist.`); });
bcs.forEach((b) => {
  if (!lp.broadConceptIds.includes(b.id)) err('P2', `Broad concept ${b.id} is not listed on the lesson plan.`);
  if (b.conceptIds.length < 2 || b.conceptIds.length > 5) err('P1', `${b.id} should split into 2 to 5 concepts (has ${b.conceptIds.length}).`);
  b.conceptIds.forEach((cid) => { if (!C[cid]) err('P2', `${b.id} lists missing concept ${cid}.`); else if (C[cid].broadConceptId !== b.id) err('P3', `${cid} says its parent is ${C[cid].broadConceptId}, but ${b.id} lists it.`); });
  if (!b.mece || !b.mece.dimension || !b.mece.rationale) err('P4', `${b.id} must state its MECE split dimension and rationale.`);
});
cs.forEach((c) => {
  const parents = bcs.filter((b) => b.conceptIds.includes(c.id));
  if (parents.length !== 1) err('P3', `${c.id} must have exactly one parent broad concept (found ${parents.length}).`);
});
if (!lp.mece || !lp.mece.dimension || !lp.mece.rationale) err('P4', 'The lesson plan must state its MECE split dimension and rationale.');

// ---------- Mutually exclusive ----------
// ME1: every objective has exactly one owner, and the owner lists it.
objs.forEach((o) => {
  const ownersListing = [lp.objectiveId === o.id ? lp.id : null, ...bcs.filter((b) => b.objectiveId === o.id).map((b) => b.id), ...cs.filter((c) => c.objectiveIds.includes(o.id)).map((c) => c.id)].filter(Boolean);
  if (ownersListing.length !== 1) err('ME1', `Objective ${o.id} must be owned by exactly one node (owned by: ${ownersListing.join(', ') || 'none'}).`);
  else if (ownersListing[0] !== o.ownerId) err('ME1', `Objective ${o.id} says owner ${o.ownerId} but is listed by ${ownersListing[0]}.`);
});
// ME2: every term is introduced by exactly one concept.
terms.forEach((t) => {
  const intro = cs.filter((c) => c.termIds.includes(t.id)).map((c) => c.id);
  if (intro.length !== 1) err('ME2', `Term "${t.en}" must be introduced by exactly one concept (found: ${intro.join(', ') || 'none'}).`);
  else if (intro[0] !== t.ownerConceptId) err('ME2', `Term "${t.en}" says owner ${t.ownerConceptId} but is introduced by ${intro[0]}.`);
});
cs.forEach((c) => c.termIds.forEach((tid) => { if (!T[tid]) err('ME2', `${c.id} introduces unknown term ${tid}.`); }));
// ME3: no duplicate objective statements or concept titles.
const dup = (arr, key, rule, label) => { const seen = {}; arr.forEach((x) => { const k = x[key].trim().toLowerCase(); if (seen[k]) err(rule, `${label} "${x[key]}" appears twice (${seen[k]}, ${x.id}).`); seen[k] = x.id; }); };
dup(objs, 'statement', 'ME3', 'Objective');
dup(cs, 'title', 'ME3', 'Concept title');
// ME4: unique ids everywhere.
const allIds = [lp.id, ...bcs.map((x) => x.id), ...cs.map((x) => x.id), ...objs.map((x) => x.id), ...terms.map((x) => x.id), ...cs.flatMap((c) => [c.workedQuestion.id, ...c.checks.map((q) => q.id), ...c.misconceptions.map((m) => m.id)])];
const idSeen = new Set(); allIds.forEach((id) => { if (idSeen.has(id)) err('ME4', `Duplicate id ${id}.`); idSeen.add(id); });

// ---------- Collectively exhaustive ----------
// CE1: the objective tree mirrors the pyramid, and every parent objective has children.
objs.forEach((o) => {
  if (o.parentId === null && o.id !== lp.objectiveId) err('CE1', `Only the apex objective may have no parent (${o.id}).`);
  if (o.parentId && !O[o.parentId]) err('CE1', `Objective ${o.id} has unknown parent ${o.parentId}.`);
});
const apex = O[lp.objectiveId];
if (!apex) err('CE1', 'Apex objective missing.');
bcs.forEach((b) => {
  const bo = O[b.objectiveId];
  if (!bo) { err('CE1', `${b.id} objective ${b.objectiveId} missing.`); return; }
  if (bo.parentId !== lp.objectiveId) err('CE1', `${b.objectiveId} must be a child of the apex objective.`);
  const childObjs = b.conceptIds.flatMap((cid) => (C[cid] ? C[cid].objectiveIds : []));
  if (!childObjs.length) err('CE1', `${b.id} objective is not covered by any concept objective.`);
  childObjs.forEach((oid) => { if (O[oid] && O[oid].parentId !== b.objectiveId) err('CE1', `Concept objective ${oid} should sit under ${b.objectiveId}.`); });
});
// CE2: every syllabus line maps to at least one existing concept, and every concept serves a syllabus line.
lp.syllabusLines.forEach((s) => {
  if (!s.conceptIds.length) err('CE2', `Syllabus line "${s.text}" is not covered by any concept.`);
  s.conceptIds.forEach((cid) => { if (!C[cid]) err('CE2', `Syllabus line ${s.id} points to missing concept ${cid}.`); });
});
cs.forEach((c) => { if (!lp.syllabusLines.some((s) => s.conceptIds.includes(c.id))) warn('CE2', `${c.id} is not tied to any syllabus line (allowed for bridge concepts, but check scope).`); });
if (!lp.mece.outOfScope || !lp.mece.outOfScope.length) warn('CE3', 'Name what is out of scope so "exhaustive" has a clear boundary.');

// ---------- Concept completeness and check mix ----------
const CONCEPT_TYPES = ['mcq', 'numerical', 'diagram'];
const ENGLISH_TYPES = ['short_english', 'spoken', 'long_written'];
cs.forEach((c) => {
  const e = c.explanation;
  if (!e || !e.text || !e.keyIdea) err('C1', `${c.id} needs an explanation with keyIdea and text.`);
  else {
    const words = e.text.split(/\s+/).length;
    if (words < 50 || words > 160) warn('C1', `${c.id} explanation is ${words} words (aim for 60 to 140).`);
    if (!e.modalities || !e.modalities.textImage || !e.modalities.textImage.diagram) err('C1', `${c.id} needs the text + image modality with a diagram.`);
    const steps = (e.modalities && e.modalities.voice && e.modalities.voice.walkthrough) || [];
    if (steps.length < 3 || steps.length > 8) err('C1', `${c.id} voice walkthrough needs 3 to 8 steps (has ${steps.length}).`);
    steps.forEach((s, i) => { if (!e.text.includes(s.target)) err('C1', `${c.id} walkthrough step ${i + 1} target "${s.target}" is not in the explanation text.`); });
    if (e.modalities && e.modalities.video && !['narrated_slides', 'generated_clip'].includes(e.modalities.video.format)) err('C1', `${c.id} video format is unknown.`);
  }
  if (!c.example || !c.example.scenario || !c.example.takeaway) err('C2', `${c.id} needs an example with a scenario and a takeaway.`);
  const w = c.workedQuestion;
  if (!w || !w.prompt || !w.modelAnswer || !w.modelAnswer.length) err('C3', `${c.id} needs a fully answered worked question.`);
  else {
    const rubricTotal = w.rubric.reduce((s, r) => s + r.marks, 0);
    if (rubricTotal !== w.marks) err('C3', `${c.id} worked question rubric adds to ${rubricTotal}, not ${w.marks}.`);
    (w.examVocabulary || []).forEach((tid) => { if (!T[tid]) err('C3', `${c.id} worked question uses unknown term ${tid}.`); });
  }
  const checks = c.checks || [];
  if (checks.length < 3) err('C4', `${c.id} needs at least 3 check questions (has ${checks.length}).`);
  if (!checks.some((q) => CONCEPT_TYPES.includes(q.type) && q.dimension === 'concept')) err('C4', `${c.id} needs a concept check (mcq, numerical or diagram).`);
  if (!checks.some((q) => q.type === 'term_match' && q.dimension === 'words')) err('C4', `${c.id} needs a words check (term_match).`);
  if (!checks.some((q) => ENGLISH_TYPES.includes(q.type) && q.dimension === 'english')) err('C4', `${c.id} needs an English check (short_english, spoken or long_written).`);
  if (c.labId && !checks.some((q) => q.dimension === 'lab')) err('C4', `${c.id} has a lab, so it needs a lab check.`);
  checks.forEach((q) => {
    q.objectiveIds.forEach((oid) => { if (!c.objectiveIds.includes(oid)) err('C5', `${q.id} tests ${oid}, which ${c.id} does not own.`); });
    if ((q.type === 'mcq' || q.type === 'term_match') && (!q.options || !q.options.includes(q.answer))) err('C5', `${q.id} answer must be one of its options.`);
    if (q.type === 'numerical' && !/\d/.test(q.answer)) err('C5', `${q.id} numerical answer needs a value.`);
  });
  if (!c.misconceptions || !c.misconceptions.length) warn('C6', `${c.id} has no misconceptions listed (they drive diagnosis and fault cards).`);
});

// ---------- Prerequisites form a DAG ----------
cs.forEach((c) => c.prerequisiteIds.forEach((p) => { if (!C[p]) err('D1', `${c.id} has unknown prerequisite ${p}.`); if (p === c.id) err('D1', `${c.id} cannot require itself.`); }));
const state = {};
function visit(id, stack) {
  if (state[id] === 'done') return;
  if (state[id] === 'active') { err('D2', `Prerequisite cycle: ${[...stack, id].join(' -> ')}`); return; }
  state[id] = 'active';
  (C[id] ? C[id].prerequisiteIds : []).forEach((p) => visit(p, [...stack, id]));
  state[id] = 'done';
}
cs.forEach((c) => visit(c.id, []));

// ---------- Totals ----------
const minutes = cs.reduce((s, c) => s + c.estMinutes, 0);
if (minutes !== lp.estMinutes) warn('T1', `Lesson plan says ${lp.estMinutes} min but concepts add to ${minutes} min.`);
(L.labs || []).forEach((lab) => lab.conceptIds.forEach((cid) => { if (!C[cid] || C[cid].labId !== lab.id) err('T2', `Lab ${lab.id} lists ${cid}, which does not point back to it.`); }));

// ---------- Report ----------
const checkCount = cs.reduce((s, c) => s + c.checks.length, 0);
console.log(`Ledger: ${lp.title}`);
console.log(`Pyramid: 1 lesson plan > ${bcs.length} broad concepts > ${cs.length} concepts; ${objs.length} objectives, ${terms.length} terms, ${cs.length} worked questions, ${checkCount} check questions, ${minutes} min.`);
warnings.forEach((w) => console.log('warning ' + w));
if (errors.length) { errors.forEach((e) => console.log('ERROR ' + e)); console.log(`${errors.length} error(s).`); process.exit(1); }
console.log('Valid: mutually exclusive, collectively exhaustive, complete.');
