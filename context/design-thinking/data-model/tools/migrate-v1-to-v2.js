#!/usr/bin/env node
/*
 * Converts a v1 lesson ledger (diode-era schema) to lesson-ledger/v2.
 * Usage: node tools/migrate-v1-to-v2.js archive-v1/diodes-and-rectifiers.ledger.json ledgers/electronics/diodes-and-rectifiers.json
 *
 * What changes: subject profile embedded; branch enum -> discipline + subjectProfileId; Odia-only -> language policy;
 * diagram -> visual; walkthrough en -> say; lab_predict -> predict; labId -> practicalId; labs -> practicals;
 * examWeight -> examSignal; language -> localization; terms en -> term, odiaGloss -> glosses.or;
 * usesTermIds computed from the explanation text; provenance and review added.
 * Additions specific to this chapter (interactives, practical steps, fault cards) are in CHAPTER_EXTRAS.
 */
const fs = require('fs');
const path = require('path');
const [src, out] = process.argv.slice(2);
if (!src || !out) { console.error('Usage: migrate-v1-to-v2.js <v1.json> <v2.json>'); process.exit(1); }
const v1 = JSON.parse(fs.readFileSync(src, 'utf8'));
const P = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'subject-profiles.json'), 'utf8'));

const BRANCH_TO_PROFILE = { Electronics: 'electronics', Electrical: 'electrical', Chemical: 'chemical' };
const profileId = BRANCH_TO_PROFILE[v1.course.branch] || 'generic';
const profile = { ...P.profiles.find((p) => p.id === profileId), checkMix: P.defaultCheckMix };
const slug = (s) => s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
const labIdMap = Object.fromEntries((v1.labs || []).map((l) => [l.id, l.id.replace(/^LAB-/, 'PR-')]));

/* Chapter-specific additions that v1 could not express. */
const CHAPTER_EXTRAS = {
  interactives: {
    'C-1.3': {
      kind: 'parameter_sweep',
      prompt: 'Drag the forward voltage and watch the current. Where does it start to rise?',
      inputs: [{ name: 'V', label: 'Forward voltage', unit: 'V', min: 0, max: 0.8, step: 0.01, default: 0.5 }],
      outputs: [{ name: 'I', label: 'Diode current', unit: 'mA', formula: '1e-14*(exp(V/0.02585)-1)*1000', decimals: 3 }],
      plot: { x: 'V', y: 'I' }
    },
    'C-2.1': { kind: 'simulation', prompt: 'Run the half-wave rectifier and look at the output.', practicalId: 'PR-RECT' },
    'C-3.2': {
      kind: 'parameter_sweep',
      prompt: 'Change the load current and the capacitor. How big is the ripple?',
      inputs: [
        { name: 'I', label: 'Load current', unit: 'mA', min: 10, max: 500, step: 10, default: 100 },
        { name: 'C', label: 'Capacitor', unit: 'µF', min: 100, max: 4700, step: 100, default: 1000 },
        { name: 'f', label: 'Ripple frequency (50 half-wave, 100 full-wave)', unit: 'Hz', min: 50, max: 100, step: 50, default: 100 }
      ],
      outputs: [{ name: 'Vr', label: 'Peak-to-peak ripple', unit: 'V', formula: '(I/1000)/(f*C*1e-6)', decimals: 2 }]
    }
  },
  externalPrerequisites: {
    'C-1.1': [{ title: 'Semiconductor basics (Class 12)', level: 'school', canonicalKey: 'semiconductor-basics' }]
  },
  practicals: {
    'LAB-RECT': {
      kind: 'simulation',
      tool: { name: 'Browser rectifier simulator', hasTour: true },
      aim: 'Build a half-wave rectifier, measure its output, then add a capacitor filter and measure the ripple.',
      apparatus: ['Transformer secondary, 12 V rms, 50 Hz', '1N4007 silicon diode', '1 kΩ load resistor', '470 µF capacitor', 'Two-channel oscilloscope'],
      steps: [
        { n: 1, instruction: 'Place the source, the diode and the 1 kΩ load in series.', showMe: true, checkpoint: 'The diode band faces the load.' },
        { n: 2, instruction: 'Probe the input on channel 1 and the load voltage on channel 2. Set both channels to DC coupling.', showMe: true },
        { n: 3, instruction: 'Draw your prediction of the output, then run the simulation.', showMe: false, checkpoint: 'Prediction saved.' },
        { n: 4, instruction: 'Measure the peak output and the DC (average) output.', showMe: false, checkpoint: 'Peak about 16.3 V, DC about 5.2 V.' },
        { n: 5, instruction: 'Add the 470 µF capacitor across the load and measure the peak-to-peak ripple.', showMe: true, checkpoint: 'Ripple about 0.7 V peak to peak.' }
      ],
      observations: { columns: ['Setup', 'Peak output (V)', 'DC output (V)', 'Ripple p-p (V)'], rows: 2 },
      expected: 'Without the capacitor: positive half-cycles only, about 16.3 V peak at 50 Hz, DC about 5.2 V. With 470 µF: output near 16 V with about 0.7 V peak-to-peak ripple.',
      faultCards: [
        { id: 'FC-RECT-1', type: 'Flipped', symptom: 'The output shows only the negative half-cycles.', cause: 'The diode is connected the wrong way round.', fix: 'Turn the diode so its band faces the load.', misconceptionRef: 'M-2.1-b', difficulty: 1 },
        { id: 'FC-RECT-2', type: 'Wrong value', symptom: 'With the filter added, the output is barely smoother than without it.', cause: 'A 10 µF capacitor was used; ripple ≈ I/(fC) is far larger than the peak.', fix: 'Use 470 µF or more for a 1 kΩ load.', difficulty: 2 },
        { id: 'FC-RECT-3', type: 'Wrong tool setting', symptom: 'The output sits around zero instead of above it.', cause: 'The oscilloscope channel is on AC coupling, which hides the DC level.', fix: 'Switch channel 2 to DC coupling.', difficulty: 2 }
      ],
      vivaPrompts: [
        'Why is the output frequency of a half-wave rectifier the same as the input frequency?',
        'What peak inverse voltage must the diode withstand here, with and without the capacitor?',
        'Why does adding a capacitor reduce the ripple?',
        'What happens to the ripple if the load resistance is halved?'
      ]
    }
  }
};

/* Content fixes found by the v2 validator (rule D3: a term used before the concept that introduces it). */
const TERM_OWNER_FIXES = { 'T-piv': 'C-2.2', 'T-reverse-saturation-current': 'C-1.2' }; // first needed (and explained) there
const EXTRA_USES = { 'C-2.3': ['T-centre-tap'] };       // the bridge answer compares itself with the centre-tap
const RUBRIC_FIXES = { 'Q-2.4-d': [{ criterion: 'Defines rectification efficiency as DC output power over AC input power', marks: 1 }, { criterion: 'States 40.6% for a half-wave rectifier', marks: 1 }] };
v1.terms.forEach((t) => { if (TERM_OWNER_FIXES[t.id]) t.ownerConceptId = TERM_OWNER_FIXES[t.id]; });
v1.concepts.forEach((c) => {
  c.termIds = c.termIds.filter((id) => !TERM_OWNER_FIXES[id] || TERM_OWNER_FIXES[id] === c.id);
  Object.entries(TERM_OWNER_FIXES).forEach(([id, owner]) => { if (owner === c.id && !c.termIds.includes(id)) c.termIds.push(id); });
  c.checks.forEach((q) => { if (RUBRIC_FIXES[q.id]) q.rubric = RUBRIC_FIXES[q.id]; });
});

const terms = v1.terms.map((t) => {
  const m = t.en.match(/^(.*?)\s*\(([A-Z]{2,})\)$/);
  const out = { id: t.id, term: m ? m[1] : t.en, definition: t.definition, ownerConceptId: t.ownerConceptId };
  if (m) out.aliases = [m[2]];
  if (t.odiaGloss) out.glosses = { or: t.odiaGloss };
  return out;
});

const misconceptionIds = new Set(v1.concepts.flatMap((c) => c.misconceptions.map((m) => m.id)));
// A term counts as used when it appears as a whole phrase, after longer terms are masked out
// (so "ripple" is not found inside "ripple factor").
const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const phrases = terms.flatMap((t) => [t.term, ...(t.aliases || [])].map((w) => ({ id: t.id, owner: t.ownerConceptId, w: w.toLowerCase() }))).sort((a, b) => b.w.length - a.w.length);
const termUsedIn = (c) => {
  let text = ' ' + (c.explanation.text + ' ' + c.workedQuestion.modelAnswer.join(' ')).toLowerCase() + ' ';
  const found = new Set();
  phrases.forEach((p) => {
    const re = new RegExp(`(^|[^a-z0-9-])${esc(p.w)}(?:s|es|d|ed|ing)?(?=[^a-z0-9-]|$)`, 'g');
    if (re.test(text)) { if (p.owner !== c.id) found.add(p.id); text = text.replace(re, '$1#'); }
  });
  (EXTRA_USES[c.id] || []).forEach((id) => found.add(id));
  return [...found];
};
const WQ_TYPE = { long_answer: 'long_written', short_answer: 'short_english' };
const splitUnit = (ans) => { const m = String(ans).match(/^\s*(-?[\d.]+)\s*([^\d\s].*)$/); return m ? m[2].trim() : undefined; };

const concepts = v1.concepts.map((c) => {
  const ex = c.explanation;
  const modalities = {
    textImage: { visual: ex.modalities.textImage.diagram },
    voice: { walkthrough: ex.modalities.voice.walkthrough.map(({ en, ...s }) => ({ ...s, say: en })) }
  };
  if (ex.modalities.video) modalities.video = ex.modalities.video;
  if (CHAPTER_EXTRAS.interactives[c.id]) modalities.interactive = CHAPTER_EXTRAS.interactives[c.id];
  const out = {
    id: c.id, broadConceptId: c.broadConceptId, order: c.order, title: c.title, canonicalKey: slug(c.title), canDo: c.canDo,
    objectiveIds: c.objectiveIds, prerequisiteIds: c.prerequisiteIds,
    ...(CHAPTER_EXTRAS.externalPrerequisites[c.id] ? { externalPrerequisites: CHAPTER_EXTRAS.externalPrerequisites[c.id] } : {}),
    termIds: c.termIds, usesTermIds: termUsedIn(c),
    misconceptions: c.misconceptions,
    explanation: { keyIdea: ex.keyIdea, text: ex.text, modalities, defaultModality: ex.defaultModality },
    example: c.example,
    workedQuestion: { ...c.workedQuestion, type: WQ_TYPE[c.workedQuestion.type] || c.workedQuestion.type },
    checks: c.checks.map((q) => {
      const nq = { ...q, type: q.type === 'lab_predict' ? 'predict' : q.type };
      if (nq.type === 'numerical' && !nq.unit) { const u = splitUnit(nq.answer); if (u) nq.unit = u; }
      if (typeof nq.tolerance === 'string') { const m = nq.tolerance.match(/([\d.]+)\s*%/); nq.tolerance = m ? { kind: 'percent', value: +m[1] } : undefined; if (!nq.tolerance) delete nq.tolerance; }
      return nq;
    }),
    ...(c.labId ? { practicalId: labIdMap[c.labId] } : {}),
    examSignal: { basis: 'estimate', askedIn: c.examWeight.askedIn, outOf: c.examWeight.outOf, note: c.examWeight.note },
    estMinutes: c.estMinutes,
    localization: { perLanguage: { or: { status: c.language.status, levels: c.language.status === 'to_generate' ? [] : c.language.dialLevels } } },
    sources: [{ origin: 'curated', label: 'Team-curated worked example for the demo' }],
    review: { status: 'auto_checked', notes: 'Passes validate.js; worked answers still need a teacher check.' }
  };
  return out;
});

const practicals = (v1.labs || []).map((l) => {
  const extra = CHAPTER_EXTRAS.practicals[l.id] || {};
  const faultCards = (extra.faultCards || []).map(({ misconceptionRef, ...f }) => (misconceptionRef && misconceptionIds.has(misconceptionRef) ? { ...f, misconceptionId: misconceptionRef } : f));
  return { id: labIdMap[l.id], title: l.title, kind: extra.kind || 'simulation', conceptIds: l.conceptIds, ...extra, faultCards, sources: [{ origin: 'curated', label: 'Team-built simulator exercise' }] };
});

const v2 = {
  schema: 'lesson-ledger/v2',
  subjectProfile: profile,
  course: {
    id: v1.course.id, title: v1.course.title, kind: 'university', programme: 'B.Tech',
    discipline: 'Electronics and Communication', subjectProfileId: profileId,
    term: { semester: v1.course.semester },
    languages: { source: 'en', support: ['or'], dial: { levels: 5, labels: ['Mostly Odia', 'Odia with English terms', 'Half and half', 'English with Odia help', 'Exam English'] } },
    examProfileId: 'EX-SAMPLE',
    lessonPlanIds: v1.course.lessonPlanIds
  },
  examProfile: {
    id: 'EX-SAMPLE', body: 'Sample first-year pattern; replace with the university\'s real pattern',
    exams: [{ kind: 'mid_sem', durationMin: 60, totalMarks: 25, pattern: [{ type: 'long_written', marks: 5, count: 5 }] }],
    englishRubricId: 'ER-DEFAULT'
  },
  englishRubric: {
    id: 'ER-DEFAULT',
    criteria: [
      { key: 'terms', label: 'Uses the exact technical terms', levels: ['Terms missing or replaced', 'Most terms used', 'Every key term used correctly'] },
      { key: 'structure', label: 'Answer is in exam order: define, explain, show, conclude', levels: ['No clear order', 'Order partly followed', 'Clear exam order'] },
      { key: 'clarity', label: 'Each sentence says one thing clearly', levels: ['Meaning is hard to follow', 'Mostly clear', 'Clear throughout'] },
      { key: 'completeness', label: 'Answers every part of the question', levels: ['Parts missing', 'One part thin', 'Every part answered'] }
    ],
    neverPenalise: ['Spelling that does not change meaning', 'Grammar that does not block meaning', 'Indian English usage', 'Handwriting style']
  },
  lessonPlan: {
    ...v1.lessonPlan, scope: 'chapter',
    sources: v1.lessonPlan.sources.map((s) => ({ origin: s.kind, label: s.label })),
    review: { status: 'auto_checked' }
  },
  broadConcepts: v1.broadConcepts,
  concepts,
  objectives: v1.objectives,
  terms,
  practicals
};
// keep key order tidy: scope right after courseId
const { id, courseId, scope, ...rest } = v2.lessonPlan; v2.lessonPlan = { id, courseId, scope, ...rest };
fs.mkdirSync(path.dirname(out), { recursive: true });
fs.writeFileSync(out, JSON.stringify(v2, null, 1) + '\n');
console.log(`Wrote ${out}: ${concepts.length} concepts, ${terms.length} terms, ${practicals.length} practical(s).`);
