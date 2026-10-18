# All CAM modules use one plug-in contract and the existing v1 envelope

Subsequent review update, 18 October 2026: the user marked scientific accuracy,
narration fidelity, Odia/pronunciation and audio quality verified. See
[review provenance](../reviews/cam-content-review-status.md). References below to pending
review describe the original package metadata, which is unchanged. Known coverage and
saved-model limitations are still recorded; browser/delivery acceptance is separate.

18 October 2026. User clarified that the complete CAM collection must be checked together,
with a reusable plug-in interface rather than an implementation loop per concept.

This supersedes the first C-AM-01-only candidate and its proposed v2 manifest. The original
handoff already specified a trusted renderer registry. Direct verification showed the
current React v1 decoder accepts a new renderer reference and marks it unsupported without
discarding the four clips. An envelope migration is unnecessary for a new renderer.

## Implemented backend contract

`--contract candidate-cam` exports all ten source-bound packages. Manifest, revision and
media-head namespaces remain v1. One new renderer family, `cam-concept-canvas/v1`, carries
the preserved scene data for the nine concepts missing a native app renderer. It selects
one of the ten kinds supported by the identical saved `cam-packets/3` model code. The
consumer vendors that reviewed module once, with a typed wrapper; it must not execute
JavaScript or formulas supplied by manifests. The shared model SHA-256 is pinned in
`contracts/cam-model-policies-v1.json` and verified before export.

The existing web C-AM-08 bilingual package and phase renderer are retained exactly. The
candidate does not replace its four English and four Odia clips with the recovered
Odia-only backend projection. Default `--contract v1` still exports the prior records
unchanged. Candidate publication remains blocked while web adoption is pending.

Concept-scoped recordings now have a real typed variant: `scope=concept`, conceptId,
ordered placardIds, renditionId, exact display/speech hashes, content-addressed audio and
the original provenance/review/timing. No invented per-placard split or timing is created.
The six recordings remain one clip each. Existing per-placard records are unchanged.

`candidate-signal` is retained for the first slice's numerical regression only; it is not
the current web implementation target. Use the all-CAM handoff.

## Web adoption required once

- Extend Python scene/narration unions, binding checks and lesson-side media pointer to
  understand the common canvas and concept-audio variants.
- Extend the matching TypeScript unions/registry, scope-aware rendition selection and
  player lifetime. Wrap the shared reviewed model once for all supported kinds.
- Separate published artifact-metadata availability from audio object-store availability.
  The current API suppresses the entire mediaExperience when assets is None, so an audio
  configuration gap also hides data-only scenes. Keep private asset fetches authenticated
  and unavailable until configured; report that availability truthfully in the UI.
- Publish prepared media through the existing publisher only after coordinated schema,
  renderer and delivery acceptance. No catalog or learner-state reimport.

## Scope and known content limitations

This makes saved content transportable/renderable after one consumer integration. It does
not approve science, pronunciation or narration quality. All review states remain pending.
English narration exists only for C-AM-08; no sentence timing exists. Preserve explicit
manual playback/navigation semantics.

The saved model is the authority for this compatibility slice, with its limitations
visible: C-AM-01 draws signal/reference (two traces although its brief describes three);
C-AM-04 fixes the carrier at 2000 Hz although its authored interaction also describes an
adjustable fc input. FM/PM are normalized teaching examples, not simulator settings.
These are review/coverage issues to resolve deliberately, not reasons to regenerate the
batch or silently invent controls. Rendering the saved model does not settle them.
