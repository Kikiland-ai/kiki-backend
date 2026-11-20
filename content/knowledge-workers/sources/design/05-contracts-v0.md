# Contracts v0: the interfaces every session builds against

Draft v0.1 · 20 Nov 2026 · Status: **Proposed**; freeze at H1 · Owner: the hub ([MISSION](MISSION.md))

These are the seams between the parallel sessions. If every session codes against them, the pieces fit at integration. **Change control:** propose a change in your session report. The hub decides and bumps the version. Additive optional fields can land without waiting; renames and removals cannot.

Shapes are written as TypeScript for the web (zod mirrors them) and apply equally to the Python side (pydantic mirrors them).

**What this build uses (v0.2, student-deep scope)**

| Section | Used in this build? | By |
|---|---|---|
| §2 Cue track | **Yes, Tier 0** | S1 (C-AM-08 narration) |
| §3 Scenes: `ece` template, `AnnotationOp` | **Yes, Tier 0** (tutor and narration cues drive the phase scene) | S1, S2 |
| §3 Scenes: `candles`, `payoff`, `line`, `flow` | Only for a Tier 2 live replay; the breadth videos draw their own visuals | S6 (reference) |
| §4 Tutor graph and turn API | **Yes, Tier 0** (student graph `ece-phase-error`) | S3, S2, S5 |
| §6 Evidence | **Yes, Tier 0** (scorecard) | S3, S2 |
| §6 Cohort | Tier 1 (organisation view) | S2 |
| §1 Domain pack | Shape reference for the builder's draft output (Tier 1) and the sector flows | S4, S5 |
| §5 Lab-lite | **Not in this build.** No Lab mode changes | — |

## 0. Conventions

```ts
type Lang = string;                            // ISO 639-1: 'en', 'or', 'hi', 'ta', 'te', 'mr', 'bn', 'kn'; BCP-47 script subtags allowed: 'hi-Latn' (romanised Hindi or Hinglish), 'or-Latn' (romanised Odia)
type LText = Partial<Record<Lang, string>>;    // must contain the pack's source language
type Dim = 'concept' | 'words' | 'english' | 'lab';  // data keys unchanged; UI labels come from the pack
type Level = 'ok' | 'partial' | 'not_yet' | 'n/a';
type Review = 'draft' | 'reviewed' | 'published';
```

- Canonical terms, numbers, units and tool labels keep their form in every language.
- Every generated text carries a review state per language. Unreviewed text displays a "machine draft" label.
- IDs are stable, ASCII and kebab or upper-case with dashes (`TR-01`, `bad-call-iv-crush`).

## 1. Domain pack

**Layout** (static files, decision A6):

```text
apps/web/public/packs/<packId>/
  pack.json              DomainPack
  graphs/<graphId>.json  TutorGraph
  audio/<file>.wav       narration and scripted tutor lines
  cohort.json            Cohort (illustrative)
  sources/               the organisation material the factory read (illustrative playbook)
```

```ts
interface DomainPack {
  schema: 'kiki-pack/v0';
  id: string;                      // 'trading-fno', 'streaming-gta', 'ece-analog-modulation'
  version: string;                 // '2026-11-21.1'
  corner: 'laws' | 'odds' | 'audiences';
  title: LText;
  persona: { name: string; role: LText; transition: LText; org: LText };
  languages: { source: Lang; learner: Lang; available: Lang[]; review: Record<Lang, Review> };
  dimensionLabels: Record<Dim, LText>;   // e.g. english → "Expression", lab → "Practice"
  modules: { id: string; title: LText; conceptIds: string[] }[];
  concepts: Concept[];
  terms: Term[];
  scenes: Scene[];
  tutorGraphs: { id: string; title: LText; file: string }[];
  labLite: LabLiteTask[];
  cohortFile?: string;
  deepLinks?: { learn?: string; do?: string };   // ECE pack points at the existing ECE screens
  provenance: { generatedBy: string; generatedAt: string; sources: SourceRef[]; review: Review; notes?: string };
}

interface Concept { id: string; title: LText; goal: LText; placards: Placard[] }   // 1–6 placards, not fixed at 4

interface Placard {
  kind: 'definition' | 'concept' | 'application' | 'recap' | 'example';
  text: LText;                     // terms marked inline as [[term-id]]; S2 maps this onto the existing termSegments helper
  sceneId?: string;
  narration?: Partial<Record<Lang, Narration>>;
  sources?: SourceRef[];
}

interface Narration {
  url: string;
  durationS: number;
  cues: CueTrack;
  timing: 'per_sentence_tts' | 'manual';   // say which, always
  script?: string[];               // the sentences, in order, as spoken
}

interface Term { id: string; term: string; meaning: LText; say?: LText; example?: LText }
interface SourceRef { id: string; title: string; locator?: string }   // "Desk playbook, p. 3"
```

## 2. Cue track (shared by the ECE sync and pack lessons)

```ts
type CueTrack = Cue[];             // sorted by t
interface Cue {
  t: number;                       // seconds from the start of the clip
  sentence?: number;               // index into Narration.script
  placard?: number;                // whole-concept clips: advance to this placard
  scene?: {
    id?: string;                   // defaults to the placard's scene
    state?: string | Record<string, number | string | boolean>;   // a named state, or values such as { phi: 60 }
    highlight?: string[];          // target ids inside the scene
    annotate?: AnnotationOp[];
    clear?: boolean;               // remove earlier annotations
  };
}
```

**Player rules.** The audio element's current time is the master clock. The active cue is the last cue with `t ≤ currentTime`. Seeking recomputes; pausing holds the current visual; changing speed changes nothing in the cue data. Reduced motion shows each state without animated transitions. Moving the slider by hand takes over from the cues until the next play.

**ECE adaptation (S1).** Cue files live beside the lesson code, keyed by narration rendition, for example `apps/web/src/features/learning/cues/<renditionId>.json`. `scene.state` values map onto existing scene props: for C-AM-08 the angle is **`phi`**, in degrees, 0–180, step 15 (`fixtures/concept-media-C-AM-08.json:328`). `highlight` uses the scene's test ids (`aligned-trace`, `recovered-trace`, `recovery-fraction`) or the authored `walkthrough` targets. Cues stay out of the hash-pinned scene and manifest files.

## 3. Scenes

Deterministic templates. The factory fills parameters, which are validated against these shapes; nobody ships generated drawing code.

```ts
type Scene =
  | { id: string; template: 'candles'; params: CandlesParams; states?: Record<string, StatePatch> }
  | { id: string; template: 'payoff';  params: PayoffParams;  states?: Record<string, StatePatch> }
  | { id: string; template: 'line';    params: LineParams;    states?: Record<string, StatePatch> }
  | { id: string; template: 'flow';    params: FlowParams;    states?: Record<string, StatePatch> }
  | { id: string; template: 'ece';     params: { renderer: 'coherent-phase-recovery/v1' | 'dsb-sc-visual/v1' | 'cam-concept-canvas/v1'; conceptId: string }; states?: Record<string, StatePatch> };   // states: v0.2, accepted 03:55

interface CandlesParams {
  bars: { t: string; o: number; h: number; l: number; c: number }[];
  events?: { id: string; at: string; label: LText }[];      // e.g. policy announcement
  levels?: { id: string; price: number; label: LText }[];   // support, resistance, entry, stop
}
interface PayoffParams {
  legs: { id: string; type: 'call' | 'put'; side: 'long' | 'short'; strike: number; premium: number; lots: number }[];
  lotSize: number; spot: number; range: [number, number];
  iv?: { before: number; after: number }; daysToExpiry?: { before: number; after: number };
}
interface LineParams {
  x: { label: LText; unit?: string; values: number[] };
  series: { id: string; label: LText; values: number[] }[];
  bands?: { id: string; from: number; to: number; label: LText }[];   // segments of a stream
  markers?: { id: string; x: number; label: LText }[];
}
interface FlowParams { nodes: { id: string; label: LText }[]; edges: { from: string; to: string; label?: LText }[] }

interface StatePatch {
  show?: string[]; hide?: string[]; highlight?: string[];
  focus?: string | [number, number];          // an id, or an x-range
  values?: Record<string, number>;            // e.g. { ivPhase: 1 } to switch payoff from "before" to "after"
}

interface AnnotationOp {
  id: string;
  kind: 'circle' | 'box' | 'arrow' | 'underline' | 'label';
  target?: string;                            // an id inside the scene, or
  at?: { x: number; y: number } | { x0: number; y0: number; x1: number; y1: number };   // data coordinates
  text?: LText;
  dim?: Dim;                                  // colours the mark by skill: green concept, red words, yellow expression, blue practice
}
```

The payoff template computes the "now" curve with Black–Scholes from `iv` and `daysToExpiry`, so a cue can show the same spot move losing money once IV falls. **For a Tier 2 live replay (v0.2):** add `rate?: number` (annual, decimal; the trader scenario uses 0.065), and give IV as a fraction (0.175 = 17.5%). State values may set `spot`, `daysToExpiry` and `ivPhase`. The breadth videos don't depend on this; they draw their own visuals.

## 4. Tutor mode

### Graph

```ts
interface TutorGraph {
  schema: 'kiki-tutor-graph/v0';
  id: string; packId: string;
  title: LText;
  problem: LText;                              // KiKi's opening framing
  caseData?: Record<string, unknown>;          // shown in the case card: the trade, the stream, the question
  metrics: { id: string; label: LText; dim: Dim }[];
  scenes?: Scene[];                            // graph-local scenes (resolved before the pack's scenes)
  start: string;
  nodes: Record<string, TutorNode>;
  nextSteps?: NextStep[];                      // scorecard suggestions, owned by content authors (v0.2)
}

interface NextStep {
  kind: 'concept' | 'lab' | 'graph'; id: string; why: LText;
  when?: { metric?: string; level?: Level; misconception?: string };   // omitted: always shown
}

interface TutorNode {
  kind: 'probe' | 'show' | 'conclusion';
  goal: string;                                // English, for the model and for reviewers
  say: LText;                                  // KiKi's scripted line
  audio?: Partial<Record<Lang, string>>;       // pre-generated audio for the scripted line
  canvas?: { sceneId: string; state?: string; annotate?: AnnotationOp[] };
  expect?: Branch[];                           // insights the user may show
  misconceptions?: Branch[];                   // wrong models the user may hold
  hints?: { say: LText; canvas?: TutorNode['canvas'] }[];   // ladder: question, nudge, worked step, answer
  chips?: { label: LText; text: string; route?: string }[];   // reply chips; `route` names the label the chip maps to, so it routes with no model call (v0.2)
  onUnclear?: 'hint' | string;                 // default: next hint rung
  onOffTopic?: 'redirect' | string;            // default: restate the node's question
  next?: string;                               // 'show' nodes auto-advance
  summary?: LText;                             // 'conclusion' nodes
}

interface Branch { id: string; desc: string; metric: string; level?: Level; next: string }
```

Graph size for the buildathon: 8–12 nodes, 2–3 misconceptions, every node reachable, every path ends at a conclusion. A validator script checks this.

**Canonical fields versus prototype extensions (v0.2).** The runtime reads `nextSteps` for scorecard suggestions and `caseData.review` for review state. The trader and streamer prototype flows also carry `scriptedPath`, `scriptedScorecard`, `videoScorecard` and `meta`, which only the videos use. Runtimes ignore unknown fields. If a Tier 2 live replay happens, S5 first maps `scriptedScorecard.next` → `nextSteps` and `meta` → `caseData.review`.

### Turn API

`POST /tutor/turn` in `apps/api`, authenticated with the Firebase ID token. Stateless: the client sends the state back each turn (decision A2).

`GET /tutor/graphs/{id}` returns the graph JSON for the UI's graph map. Graphs are bundled with the API in this build.

```ts
interface TurnRequest {
  graphId: string;                             // '<packId>/<graphId>'
  lang: Lang;
  state: TutorState | null;                    // null starts the graph
  input: { text: string } | { audioBase64: string; mime: string } | null;   // null continues a 'show' node
  clientTurnId: string;                        // idempotency
}
interface TutorState { node: string; hintLevel: number; path: string[]; evidence: EvidenceEvent[]; turn: number }

interface TurnResponse {
  state: TutorState;
  kiki: { ack?: string; say: string; audio?: string | null };   // ack: at most one model-written sentence
  canvas: TutorNode['canvas'] | null;
  route: { label: string; matched: string[]; misconception: string | null; confidence: number; quote?: string } | null;
  done: boolean;
  scorecard: null | {
    metrics: { id: string; level: Level; evidence: string[] }[];
    next: { kind: 'concept' | 'lab' | 'graph'; id: string; why: LText }[];
  };
  timing: { modelMs: number };
}
```

**Routing rules (v0.2).**
- A chip reply with a `route` routes directly; chip replies earn no words or expression evidence.
- After the last hint rung, the runtime advances through the node's **first** `expect` branch and records level `not_yet` for that metric. Authors list the `ok` branch first.
- Each node's `canvas` replaces the previous scene state and annotations. A node without `canvas` keeps the current scene.
- During a probe, the UI locks the scene's controls and applies the state's `hide` list, so the scene can't print the answer. It unlocks after the conclusion.

**The model call.** One Gemini request per turn with a response schema whose `label` enum is the current node's `expect` ids, its `misconceptions` ids, `unclear` and `off_topic`. Return also `quote` (the user's words that justify the label), `confidence`, and `expression: { clarity: 0 | 1 | 2, termsUsed: string[] }` for words and expression evidence. The graph decides the transition. The model never chooses a node.

## 5. Lab-lite

`POST /lablite/look` in `apps/api`, authenticated. One call per user request; no polling.

```ts
interface LabLiteTask {
  id: string; tool: LText;                     // "Stream analytics dashboard"
  userAsk: LText;                              // "Why did viewers drop here?"
  lookFor: { id: string; desc: string }[];     // allowed finding ids, injected into the response schema
  askAfter: LText;                             // KiKi's one follow-up question
  graphId?: string;                            // optional hand-off into tutor mode
}

interface LookRequest {
  packId: string; taskId: string; lang: Lang;
  image: { base64: string; mime: 'image/jpeg' | 'image/png'; width: number; height: number };   // ≤1600 px on the long side
  question?: string;
}
interface LookResponse {
  findings: { id: string; kind: 'circle' | 'box' | 'arrow'; box: [number, number, number, number];   // [ymin, xmin, ymax, xmax] on a 0–1000 grid
              label: LText; note: LText; confidence: number }[];
  say: LText;
  unknown: string | null;                      // "I can't see the viewer graph. Scroll it into view."
  timing: { modelMs: number };
}
```

Below a confidence threshold KiKi does not draw. It says what it cannot see. That is the October rule: pointing at the wrong thing destroys trust.

## 6. Evidence and cohort

```ts
interface EvidenceEvent {
  id: string; packId: string;
  source: 'tutor' | 'lab-lite' | 'lesson-check' | 'lab';
  refId: string;                               // graph node, task or question id
  metric?: string; dim: Dim; level: Level;
  quote?: string; at: string;                  // ISO time
}

interface Cohort {
  schema: 'kiki-cohort/v0'; packId: string; label: LText;
  illustrative: true;                          // the organisation view shows "Illustrative cohort" while this is true
  skills: { id: string; label: LText; conceptIds?: string[] }[];
  learners: { alias: string; skills: Record<string, Partial<Record<Dim, Level>>> }[];
}
```

Only dimension-level evidence reaches the organisation view. Screens and transcripts stay with the learner.
