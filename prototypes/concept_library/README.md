# Stored concept content and publication pipeline

## Current: all ten modules, one plug-in contract

Use [the all-CAM handoff](../../docs/handoffs/all-cam-compatibility.md). `candidate-cam`
exports all ten scenes and 26 recordings, preserving the web C-AM-08 bilingual package.
It retains the existing v1 envelope, adds one common canvas renderer family and an honest
concept-audio variant. This supersedes the C-AM-01-only/v2 proposal. Current web consumer
unions/renderer/player integration still need the shared update; candidate apply is blocked.

```sh
python -X utf8 -B scripts/publish-concept-library.py --web-root /path/to/kiki-web --contract candidate-cam --output work/all-cam
```

## Learning compatibility continuation — 18 October

The default v1 export is unchanged. An export-only `--contract candidate-signal` now adds
C-AM-01's typed `signal-parameters/v1` scene alongside its four existing clips. The
current web consumer still requires its coordinated decoder/renderer update; candidate
publication is blocked. Whole-concept narration is still excluded pending its separate
audio-scope contract. See [the implementation handoff](../../docs/handoffs/learning-content-compatibility.md)
for schemas, conformance examples, checks and exact Mac acceptance steps.

```sh
python -X utf8 -B scripts/publish-concept-library.py --web-root /path/to/kiki-web --concepts C-AM-01 --contract candidate-signal --output work/cam01-candidate
```

The complete ten-concept batch is available as a versioned **SQLite metadata
database plus immutable asset files**, ready to query after cloning. It contains
40 authored English/mixed Odia–English placards, 22 recordings (793.8 seconds),
ten semantic scenes and the working browser renderers/posters. No provider call
is needed to read or import the saved batch.

Database: `artifacts/cam-review/concept-library.sqlite3`.
Assets and original packets: `artifacts/cam-review/site/dist/concepts/`.
SQLite holds content, scene data and references; WAV/SVG/JS bytes remain files.
The WAVs are stored with Git LFS: run `git lfs pull` if they arrive as pointer files.
The recovery manifest hashes the preserved Site source. The database builder
verifies text/speech/audio hashes and atomically builds a repeatable snapshot.
Reads are read-only and recheck packet/asset checksums.

```sh
python -B scripts/concept-library.py list
python -B scripts/concept-library.py get C-AM-08
python -B scripts/concept-library.py build
python -B scripts/verify-cam-review.py
python -m http.server 8000 --directory artifacts/cam-review/site/dist
```

The `build` command imports the saved packets into SQLite; it does not synthesize
new topics. SQL tables: `packets`, `current_packets`, `narration`, `artifacts`,
`assets`, `library_meta`. This is a Git-versioned snapshot, not a multiwriter
production service. Media revisions remain immutable in the app's Firestore.

The backend can read the library directly:

```python
from prototypes.concept_library.library import ConceptLibrary

library = ConceptLibrary()
try:
    packet = library.packet("C-AM-08")
    clip = packet["narration"][0]
    audio_bytes, content_type = library.asset(clip["audioSha256"])
finally:
    library.close()
```

Authorize requests in the existing API before exposing media. This local read
adapter does not replace enrollment/authentication or start an unauthenticated
application server.

## Feed the merged kiki-web publisher

`kiki-web` main was inspected at `93cce9b` (PR #5 merged). Its `apps/api`
already owns media schemas, publication, private storage, manifest delivery and
authorized audio reads. The adapter calls that implementation directly rather
than introducing a competing Firestore namespace or duplicating its publisher.

In the environment containing the web API dependencies (`pip install -e
/path/to/kiki-web/apps/api`), run:

```sh
python -B scripts/publish-concept-library.py --web-root /path/to/kiki-web --output work/concept-media-export
```

This validates against the actual merged catalog, lessons and Pydantic media
contract, then exports app-native `concept-media-revision/v1` records and a
`compatibility.json` report. It writes no cloud data. The exported records
reference the same content-addressed files available through `ConceptLibrary`.

The current app contract accepts per-placard narration and only the
`coherent-phase-recovery/v1` artifact. Thus C-AM-01/02/03/08 contribute 16
compatible recordings and C-AM-08 contributes the native phase scene. Other
scenes and six whole-concept recordings remain fully stored/queryable in SQLite;
they are explicitly listed as excluded from this v1 projection. The adapter
does not invent placard timings or mislabel full recordings as per-placard audio.
An all-concept `--apply` stops before writing when any concept has no compatible
media. To expose those remaining assets through the app, extend its allowlisted
scene/audio-scope contract or generate actual per-placard recordings.

Once existing cloud access is connected and the bucket is selected, publication
can use the merged publisher without regenerating the stored content:

```sh
python -B scripts/publish-concept-library.py --web-root /path/to/kiki-web --concepts C-AM-01 C-AM-02 C-AM-03 --apply --project builder-cup-a8479 --bucket EXISTING_PRIVATE_BUCKET
```

For an already-published concept, inspect its current media head first and use
`--concepts C-AM-08 --expected-current cm-EXACT_EXISTING_REVISION` for an explicit
single-concept replacement. C-AM-08's existing app package includes English
audio, while this recovered batch has Odia audio only: do not replace it without
considering that difference. Default publication refuses a conflicting head.

Firestore uses the existing app namespace:
`conceptMedia/LP-ANALOG-MODULATION/catalogVersions/{catalogVersion}/concepts/{conceptId}/revisions/{mediaRevision}`.
Private object paths use the existing app's `concept-media/.../assets/sha256/`.
Assets upload before media head activation. The source catalog version and
learner progress are not reimported or changed. Production upload is deferred;
real cloud publication is not verified by this branch.

## Provenance and remaining work

These packets reuse the exact authored mixed text and existing speech adapters.
They are scientific/native-Odia/pronunciation drafts, with no sentence alignment.
C-AM-01/02/03/08 have per-placard recordings; the others have whole-concept
recordings. Per-clip model/hash provenance is saved. Original per-clip timestamps
were not preserved by the Site export, so the app projection explicitly records
`not_recorded_in_recovered_packet` rather than inventing a timestamp. Packet
assembly timestamps remain in the original packet.

This checkout was reset before the commit request. The durable Site source and
all output packets were recovered, but earlier uncommitted Python generation
orchestration was unavailable. The original committed mixed-script/TTS adapters
are intact. This branch adds a working storage/import/publication adapter; it
does not claim to recover that missing generation code. Details and source
revision are in `docs/handoffs/concept-canvas-continuation.md`.
