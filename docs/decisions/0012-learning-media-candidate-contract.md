# Learning media: preserve v1 and export a coordinated candidate

**Superseded:** [decision 0013](0013-all-cam-plug-in-contract.md) retains the v1 envelope and
covers all ten modules with one common canvas contract. The v2 proposal below is historical
and must not drive the web implementation. Concept-scope audio is now implemented in the
batch candidate; no generation or timing fabrication was required.

18 October 2026. Status: backend candidate implemented; web adoption pending.

The Mac integration report establishes working transport and limited live lab guidance,
not completed learning/audio/artifact acceptance. The next priority is to reuse the ten
saved concept packets rather than regenerate content. The existing web publisher remains
the owner of immutable publication, authentication and private asset delivery.

## First slice

The new `signal-parameters/v1` contract projects C-AM-01's saved signal scene into data:
bounded controls, units, readouts, reference-wave semantics, source/model hashes and
numerical conformance vectors. The projector validates against the actual web catalog and
checks the stored scene/model assets through the library's checksum-checked read API.
No packet JavaScript or string formula is executed by the projector or intended consumer.

The web v1 manifest only accepts its phase-recovery scene. Silently inserting signal data
into that published envelope would break readers. Therefore:

- Default `--contract v1` preserves existing records/revisions byte-for-byte.
- Explicit `--contract candidate-v2` exports `concept-media-manifest/v2` and
  `concept-media-revision/v2`, reusing the web's existing narration and legacy phase types.
- Candidate exports report that a web contract/renderer change is required; they are not
  advertised as compatible with the current app.
- `--contract candidate-v2 --apply` is rejected before cloud imports or writes.
- No new publisher, cloud collection or delivery endpoint is introduced.

This candidate v2 implements the signal scene only. Narration still uses the existing
per-placard representation. Six concept-scope recordings remain explicitly excluded;
the next audio-scope contract below is a proposal, not an implemented capability.

The existing C-AM-08 backend v1 revision stays `cm-09967975820d6468c9272a38`. Its recovered
batch has Odia audio only. The separate web package contains English as well; do not
replace that package with an Odia-only projection as part of this work.

## Next audio-scope proposal — coordinate before implementation

Preserve existing per-placard rendition decoding. Add a separate concept-scoped variant:

```json
{
  "scope": "concept",
  "renditionId": "C-AM-04.concept.or",
  "conceptId": "C-AM-04",
  "placardIds": ["CARD-AM-04-definition", "CARD-AM-04-concept", "CARD-AM-04-application", "CARD-AM-04-recap"],
  "lang": "or",
  "timing": {"kind": "clip_duration_only", "alignment": "not_performed"}
}
```

The example omits asset/provenance/review fields for brevity; the real variant must retain
all of them. The ordered placard list must exactly match the covered lesson scope without
duplicates. Bind display and speech hashes to the exact corresponding texts joined with
a single ASCII space in that order, matching the saved packet's existing hash rule.
Require the rendition's concept to match the manifest and verify asset hash/measurements.

Use one recording across manual placard navigation, preserving playback position for
that same rendition. Do not pretend it is four clips, synthesize seek boundaries, or
animate sentence highlighting. Language changes select an actually available rendition
or report absence. The UI must pause/clean up on concept exit and avoid overlapping
players. A new schema/consumer receipt is required before these clips can be published.

## Review and deployment boundary

Numeric conformance is not a scientific/native-Odia/listening approval. The scene and
audio retain pending/unreviewed statuses. No generation, cloud changes, source-catalog
reimport, learner writes, release merge or modification of the running lab checkout is
part of this slice.
