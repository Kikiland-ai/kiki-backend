# KikiWalkthrough

Kiki explains a lesson card: a caption bar plays the narration one sentence at a time while Kiki's pointer moves through the paragraph and the diagram, marking the word or idea each sentence is about.

**Consumer provides:** `data` (`{paragraph, steps, figure?}`): `paragraph` is strings plus `{id, text, phrase?}` targets; each step is `{target, action, dim, odia, en, to?}`. Optional `autoPlay`, `stepMs` (default 3800). Without `data` it plays the diode sample.

How Kiki marks a word. One action per narration sentence, in the colour of the skill being taught (`dim`):

| Action | Looks like | Use for |
| --- | --- | --- |
| sweep | an underline draws itself left to right under the word as Kiki says it | first mention of a term |
| marker | a highlighter stroke behind the word; the rest of the paragraph dims to 40% | the one idea of this sentence |
| lens | the word is marked and a lens card opens below it: the word at 28px, its Odia meaning, Hear it | a new or hard technical term |
| connect | the word is marked and a dashed line runs from it to the matching point on the diagram, which pulses | linking a word to the graph or circuit |
| circle | a hand-drawn loop around the word | exam vocabulary or a word to say exactly |

Colours: technical words red (Words), ideas and phrases blue (Concept), exam English yellow (English), lab controls green (Lab). Text is never enlarged in place, so the paragraph never reflows. Only the lens zooms.

- Do: write one sentence per step, at most 18 words, Odia first with the English line under it, following the dial.
- Do: let the student pause, step back and tap any word at any time; the walkthrough is a guide, not a video.
- Don't: mark more than one target at once, or chain more than 8 steps on one card.
