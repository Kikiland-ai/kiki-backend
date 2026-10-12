import type * as React from 'react';

export type Dimension = 'concept' | 'words' | 'english' | 'lab';
export type DimensionValues = Partial<Record<Dimension, number>>;
export type TermState = 'new' | 'collected' | 'owned';
export interface GlossaryEntry { odia: string; example?: string }
export type Segment = string | { term: string };

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> { variant?: 'filled' | 'tonal' | 'text'; icon?: string }
export declare function Button(props: ButtonProps): React.ReactElement;

export interface KikiProps { state?: 'idle' | 'listening' | 'thinking' | 'speaking' | 'pointing' | 'asking' | 'celebrating' | 'unsure' | 'examiner'; size?: number; lead?: Dimension; direction?: number; label?: string; className?: string }
export declare function Kiki(props: KikiProps): React.ReactElement;

export interface MasteryRingProps { values?: DimensionValues; size?: number; stroke?: number; locked?: Dimension[]; flicker?: boolean; label?: string; children?: React.ReactNode; className?: string }
export declare function MasteryRing(props: MasteryRingProps): React.ReactElement;

export interface LanguageDialProps { value?: 1 | 2 | 3 | 4 | 5; defaultValue?: 1 | 2 | 3 | 4 | 5; onChange?: (value: number) => void; suggested?: number | null; onAcceptSuggestion?: (value: number) => void; className?: string }
export declare function LanguageDial(props: LanguageDialProps): React.ReactElement;

export interface TermChipProps { term: string; entry?: GlossaryEntry; state?: TermState; pulse?: boolean; onOpen?: (term: string) => void }
export declare function TermChip(props: TermChipProps): React.ReactElement;

export interface MorphTextProps { level: number; levels?: Segment[][]; glossary?: Record<string, GlossaryEntry>; termStates?: Record<string, TermState>; onTermOpen?: (term: string) => void; className?: string }
export declare function MorphText(props: MorphTextProps): React.ReactElement;

export interface WordStickerProps { term: string; entry?: GlossaryEntry; state?: TermState; className?: string }
export declare function WordSticker(props: WordStickerProps): React.ReactElement;

export interface LessonProgressProps { values?: DimensionValues; className?: string }
export declare function LessonProgress(props: LessonProgressProps): React.ReactElement;

export interface DiodeExplorableProps { defaultVoltage?: number; id?: string; className?: string }
export declare function DiodeExplorable(props: DiodeExplorableProps): React.ReactElement;

export interface DiagnosisCardProps { variant: 'solid' | 'language' | 'concept'; title?: string; message?: string; actionLabel?: string; onAction?: () => void; className?: string }
export declare function DiagnosisCard(props: DiagnosisCardProps): React.ReactElement;

export interface VoiceScopeProps { prompt?: string; transcript?: React.ReactNode; feedback?: string; defaultState?: 'ready' | 'recording' | 'playback' | 'feedback'; className?: string }
export declare function VoiceScope(props: VoiceScopeProps): React.ReactElement;

export interface ReceiptEntry { time: string; answer: string; verdict?: string }
export interface ReceiptCompareProps { before?: ReceiptEntry; after?: ReceiptEntry; className?: string }
export declare function ReceiptCompare(props: ReceiptCompareProps): React.ReactElement;

export interface MapNodeProps { label: string; odia?: string; state?: 'locked' | 'available' | 'progress' | 'mastered' | 'flicker' | 'repair'; values?: DimensionValues; heat?: string; here?: boolean; onClick?: () => void; className?: string }
export declare function MapNode(props: MapNodeProps): React.ReactElement;

export interface SnackbarProps { message: React.ReactNode; tone?: 'route'; icon?: string; actionLabel?: string; onAction?: () => void; className?: string }
export declare function Snackbar(props: SnackbarProps): React.ReactElement;

export interface SourceTagProps { label?: string; source?: string; snippet?: string; conflict?: string }
export declare function SourceTag(props: SourceTagProps): React.ReactElement;

export interface PredictionCanvasProps { expected?: 'halfwave' | 'fullwave' | 'sine' | ((x: number) => number); onResult?: (similarity: number) => void; className?: string }
export declare function PredictionCanvas(props: PredictionCanvasProps): React.ReactElement;

export interface LabStepperProps { current?: number; steps?: string[]; title?: string; hint?: string; kikiState?: KikiProps['state']; onNext?: () => void; nextLabel?: string; className?: string }
export declare function LabStepper(props: LabStepperProps): React.ReactElement;

export interface SpotlightProps { active?: boolean; style?: React.CSSProperties; className?: string; children?: React.ReactNode }
export declare function Spotlight(props: SpotlightProps): React.ReactElement;
export declare namespace Spotlight { function Target(props: { children?: React.ReactNode }): React.ReactElement }

export interface FaultCardProps { type?: 'Flipped' | 'Wrong value' | 'Missing piece' | 'Wrong connection' | 'Wrong tool setting' | 'Wrong measurement' | 'Wrong assumption'; symptom?: string; questions?: string[]; fixed?: boolean; fixedMessage?: string; onFixed?: () => void; className?: string }
export declare function FaultCard(props: FaultCardProps): React.ReactElement;

export interface SnapIssue { kind: 'mark' | 'tip'; odia: string; fix: string; cost: string }
export interface SnapLine { tick?: { label: string; ok: boolean }; parts: Array<string | { issue: number; text: string }> }
export interface AnswerOverlayProps { data?: { question: string; score: { concept: string; english: string }; lines: SnapLine[]; issues: SnapIssue[] }; className?: string }
export declare function AnswerOverlay(props: AnswerOverlayProps): React.ReactElement;

export interface ClassPulseBarProps { label: string; mastered?: number; language?: number; concept?: number; students?: number; hidden?: boolean; className?: string }
export declare function ClassPulseBar(props: ClassPulseBarProps): React.ReactElement;

export type KikiPointerState = 'idle' | 'pointing' | 'tapping' | 'dragging' | 'tracing' | 'thinking' | 'asking' | 'listening' | 'celebrating' | 'unsure' | 'waiting';
export interface KikiPointerProps { state?: KikiPointerState; size?: number; lead?: Dimension; flip?: boolean; label?: string; className?: string; style?: React.CSSProperties }
export declare function KikiPointer(props: KikiPointerProps): React.ReactElement;

export interface WalkStep { target: string; action: 'sweep' | 'marker' | 'lens' | 'connect' | 'circle'; dim: Dimension; odia?: string; en: string; to?: string }
export interface KikiWalkthroughProps { data?: { paragraph: Array<string | { id: string; text: string; phrase?: boolean }>; steps: WalkStep[]; figure?: false }; autoPlay?: boolean; stepMs?: number; className?: string }
export declare function KikiWalkthrough(props: KikiWalkthroughProps): React.ReactElement;

export interface LabGuideProps { className?: string }
export declare function LabGuide(props: LabGuideProps): React.ReactElement;

export interface PracticeQuestion { n: string; topic: string; got: number; max: number; english: number; note: string }
export interface PracticeReportProps { data?: { title: string; time: string; total?: number; questions: PracticeQuestion[] }; onOpen?: (q: PracticeQuestion) => void; onRepair?: (() => void) | false; className?: string }
export declare function PracticeReport(props: PracticeReportProps): React.ReactElement;

declare global {
  interface Window {
    Breadboard: {
      Button: typeof Button; Kiki: typeof Kiki; MasteryRing: typeof MasteryRing; LanguageDial: typeof LanguageDial; TermChip: typeof TermChip;
      MorphText: typeof MorphText; WordSticker: typeof WordSticker; LessonProgress: typeof LessonProgress; DiodeExplorable: typeof DiodeExplorable;
      DiagnosisCard: typeof DiagnosisCard; VoiceScope: typeof VoiceScope; ReceiptCompare: typeof ReceiptCompare; MapNode: typeof MapNode;
      Snackbar: typeof Snackbar; SourceTag: typeof SourceTag; PredictionCanvas: typeof PredictionCanvas; LabStepper: typeof LabStepper;
      Spotlight: typeof Spotlight; FaultCard: typeof FaultCard; AnswerOverlay: typeof AnswerOverlay; ClassPulseBar: typeof ClassPulseBar;
      KikiPointer: typeof KikiPointer; KikiWalkthrough: typeof KikiWalkthrough; LabGuide: typeof LabGuide; PracticeReport: typeof PracticeReport;
      samples: { glossary: Record<string, GlossaryEntry>; diodeLevels: Segment[][]; levelNames: string[] };
    };
  }
}
