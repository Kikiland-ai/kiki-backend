/**
 * Lesson plan data model: a MECE pyramid.
 *
 *   LessonPlan (apex: one chapter, one governing question)
 *     └─ BroadConcept (2 to 5, split along ONE stated dimension, mutually exclusive)
 *          └─ Concept (2 to 5 per broad concept; one node on the student's map)
 *               ├─ explanation  (text + image always; voice walkthrough; optional video)
 *               ├─ example
 *               ├─ workedQuestion (a fully answered exam-style question with its rubric)
 *               └─ checks[]     (a mix that tests concept, words and English; lab when there is one)
 *
 * MECE is enforced through objectives and terms:
 *   - Mutually exclusive: every Objective and every Term has exactly ONE owner concept.
 *   - Collectively exhaustive: every parent objective is covered by at least one child objective,
 *     and every syllabus line maps to at least one concept.
 * validate.js checks all of this, plus content completeness and the check mix.
 *
 * English is the source of truth. Odia and the five dial levels are generated from it
 * and must be reviewed before they ship (LanguageVariants.status).
 */

export type Id = string; // "LP-DR", "BC-2", "C-2.1", "O-2.1", "T-ripple-factor", "Q-2.1-a"
export type Dimension = 'concept' | 'words' | 'english' | 'lab';
export type Bloom = 'remember' | 'understand' | 'apply' | 'analyse' | 'evaluate' | 'create';

export interface Course {
  id: Id;
  title: string;            // "Basic Electronics"
  branch: 'Electronics' | 'Electrical' | 'Chemical';
  semester: number;
  sourceLanguage: 'en';
  studentLanguage: 'or';    // Odia first; other languages later
  lessonPlanIds: Id[];
}

/** The apex of the pyramid: one chapter. */
export interface LessonPlan {
  id: Id;
  courseId: Id;
  title: string;
  governingQuestion: string;   // the one question the whole chapter answers
  canDo: string;               // what the student can do at the end
  objectiveId: Id;             // the apex objective (O-0)
  mece: MeceSplit;             // how the chapter splits into broad concepts
  broadConceptIds: Id[];       // in teaching order
  syllabusLines: SyllabusLine[];
  estMinutes: number;          // sum of concept minutes
  sources: Source[];
}

/** One split in the pyramid, stated so a reviewer can check it. */
export interface MeceSplit {
  dimension: string;           // the single axis of the split, e.g. "stage of the AC-to-DC power-supply chain"
  rationale: string;           // why the parts don't overlap and nothing is missing
  outOfScope: string[];        // named exclusions, so "exhaustive" has a clear boundary
}

export interface BroadConcept {
  id: Id;
  lessonPlanId: Id;
  order: number;
  title: string;
  governingQuestion: string;
  objectiveId: Id;             // owned objective, child of the apex objective
  mece: MeceSplit;             // how this broad concept splits into concepts
  conceptIds: Id[];
}

/** A mini concept: one node on the student's map, one lesson of about 10 to 15 minutes. */
export interface Concept {
  id: Id;
  broadConceptId: Id;
  order: number;
  title: string;
  canDo: string;               // student-facing can-do sentence, shown on the promise card
  objectiveIds: Id[];          // objectives this concept OWNS (exclusive)
  prerequisiteIds: Id[];       // other concept ids; must form a DAG
  termIds: Id[];               // terms this concept INTRODUCES (exclusive)
  misconceptions: Misconception[];
  explanation: Explanation;
  example: Example;
  workedQuestion: WorkedQuestion;
  checks: CheckQuestion[];     // the mix rule is in validate.js
  labId?: Id;
  examWeight: { askedIn: number; outOf: number; note?: string };
  estMinutes: number;
  language: LanguageVariants;
}

export interface Objective {
  id: Id;
  statement: string;           // measurable: "Explain…", "Calculate…", "Draw…"
  bloom: Bloom;
  parentId: Id | null;         // null only for the apex objective
  ownerId: Id;                 // LessonPlan, BroadConcept or Concept id (exactly one)
}

export interface Term {
  id: Id;
  en: string;                  // canonical English term, never translated
  definition: string;
  odiaGloss?: string;          // explanation in Odia, needs native-speaker review
  ownerConceptId: Id;          // the concept that introduces it
}

export interface Misconception {
  id: Id;
  statement: string;           // what students wrongly believe
  correction: string;
  faultType?: 'Flipped' | 'Wrong value' | 'Missing piece' | 'Wrong connection' | 'Wrong tool setting' | 'Wrong measurement' | 'Wrong assumption';
}

/** The explanation, available in several modalities from one English source. */
export interface Explanation {
  keyIdea: string;             // one sentence: the thing to remember
  text: string;                // canonical English explanation, 60 to 140 words
  modalities: {
    textImage: { diagram: Diagram };                          // always present
    voice: { walkthrough: WalkStep[] };                       // KikiWalkthrough script, 3 to 8 steps
    video?: { format: 'narrated_slides' | 'generated_clip'; durationSec: number; beats: string[] };
  };
  defaultModality: 'textImage' | 'voice' | 'video';
}

export interface Diagram {
  kind: 'circuit' | 'graph' | 'waveform' | 'block' | 'physical';
  description: string;         // what to draw (brief for the illustrator or image model)
  alt: string;                 // accessible text
}

export interface WalkStep {
  target: string;              // the word or phrase in the explanation text that Kiki marks
  mark: 'sweep' | 'marker' | 'lens' | 'connect' | 'circle';
  dim: Dimension;              // colour: words red, concept blue, english yellow, lab green
  en: string;                  // the narration sentence (Odia generated from this)
}

export interface Example {
  title: string;
  scenario: string;            // a concrete, real situation
  takeaway: string;            // what the example proves about the concept
}

/** A worked, fully answered exam-style question: the model the student learns to write. */
export interface WorkedQuestion {
  id: Id;
  prompt: string;
  type: 'long_answer' | 'numerical' | 'short_answer' | 'diagram';
  marks: number;
  modelAnswer: string[];       // the answer as the student should write it, line by line
  rubric: { criterion: string; marks: number }[]; // concept marks; English is judged separately
  examVocabulary: Id[];        // term ids the answer must use correctly
}

/** A question that tests whether the concept is clear. */
export interface CheckQuestion {
  id: Id;
  type: 'mcq' | 'numerical' | 'term_match' | 'short_english' | 'spoken' | 'long_written' | 'diagram' | 'lab_predict';
  dimension: Dimension;
  prompt: string;
  options?: string[];
  answer: string;              // the correct option, value with unit, or a model answer
  tolerance?: string;          // for numericals, e.g. "±2%"
  explanation: string;         // why, shown after answering
  objectiveIds: Id[];          // must be objectives owned by this concept
  difficulty: 1 | 2 | 3;
  marks?: number;
}

export interface LanguageVariants {
  status: 'to_generate' | 'generated' | 'reviewed';
  dialLevels: (1 | 2 | 3 | 4 | 5)[];
  reviewer?: string;
}

export interface SyllabusLine {
  id: Id;
  text: string;                // as written in the syllabus
  conceptIds: Id[];            // collectively exhaustive: at least one concept
}

export interface Source {
  kind: 'curated' | 'student_notes' | 'syllabus' | 'past_paper' | 'textbook';
  label: string;
}

/** The whole ledger file. */
export interface Ledger {
  version: string;
  course: Course;
  lessonPlan: LessonPlan;
  broadConcepts: BroadConcept[];
  concepts: Concept[];
  objectives: Objective[];
  terms: Term[];
  labs: { id: Id; title: string; conceptIds: Id[] }[];
}
