# Known source and capability gaps

## One pre-existing missing local reference

The imported `design-thinking/docs/ux/student-journey-odia-ece.md` links to:

`../../../UX Working Doc — Bilingual STEM Learning (AI Builder Cup).md`

That file was not in the Design-Thinking checkout or pinned commit; its link already pointed outside the source repository. It cannot be carried over as an available source. The five local exports in `design-thinking/docs/working-doc/` and the latest `docs/ux/` journey remain available. They are not silently represented as the missing file. Ask the project owner for that source only if its contents become necessary.

Private live Claude artifacts are referenced but were not retrieved. Their URLs are not imported document contents. The source snapshot preserves all working relative links; it does not invent files for inaccessible references.

## Product capability trials still pending

- Mixed Odia–English synthesis has completed real trials; scientific/native-Odia/pronunciation review, a reviewed pronunciation lexicon and reliable timing cues remain pending. Current results and limitations are recorded in `docs/plans/active.md` and the versioned evidence archive.
- Scientific/linguistic review of generated graphics and placeholder Odia.
- A synchronized media player beyond the old fixed-timer walkthrough.
- Selection and execution of the proposed DSB-SC experiment in Simulink Online.
- A supported real-tool observation/highlighting connection; the existing lab guide is an in-app mock.
- FastAPI runtime, worker/job persistence and datastore/authorization integration remain unimplemented. Gemini access was verified in the trial runtime, but credentials/quota/model access must be checked separately in each runtime; they do not transfer through the repository.

These are explicit tasks to resolve, not hidden prerequisites treated as already complete. Keep fixture/live status and trial results in `docs/plans/active.md`.

## Resolved during source carryover

The earlier prototype review identified old component colour assignments. The carryover now includes the component guides, bundles, tokens, and Kiki artwork updates through `73d16c0`, aligning green with concept and blue with practical. This source update does not establish speech timing, general image markup, or real-tool guidance.
