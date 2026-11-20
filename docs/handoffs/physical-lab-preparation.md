# Component connection hints — 21 November 2026

Hover a numbered marker or physical socket to see an immediate cursor-adjacent
tooltip with its number, name, apparatus section and role. Current-step hints
identify the source and destination, then update after selecting the source.
The floating guide shows component names only, so students find the corresponding
parts by exploring the apparatus. Numbers stay on circuit markers and hover hints.
Keyboard focus shows the same hints;
tooltips stay within the visible workspace and remain in the fullscreen subtree.
Hover and focus do not submit experiment actions.

Verified the source and destination hints in native Chrome without advancing
the saved experiment. Twelve JavaScript checks pass, including hover coordinate
forwarding, connection cues and tooltip bounds; all 20 focused Python tests pass,
including serving the new hints module. Generated contracts are current.

# Direct experiment demo — 21 November 2026

The default preview now starts the hands-on DSB-SC experiment without prerequisite
quizzes or a demonstration click-through. Open the local preview and choose
**Start experiment**. The normal preparation UI remains available at
`/v1/physical-labs/preview?mode=preparation`; its prerequisite policy is unchanged.

- The bottom-right Fullscreen control expands the apparatus workspace. The Kiki
  guide, camera controls, markers, readings and output graphs remain inside it.
  Exit via the same control or Escape. An expanded-page fallback is available
  when the browser cannot enter native fullscreen.
- Kiki's floating guide shows the current action and its two connection targets.
  Select the output socket and then the input socket directly on the apparatus.
  The backend checks the exact connection and automatically advances after a
  correct action. Incorrect actions remain on the current step.
- The guide moves away from required sockets automatically. Drag its header to
  place it manually. Arrow keys move the focused header; Home restores automatic
  placement. It can be collapsed without ending the experiment.
- The null-adjustment step exposes its slider/numeric control in the guide.
  Measurement steps show the current virtual reading and a Record reading action.
- Live plots and the 3D CRO use the backend's actual trace arrays. Moving the
  probe changes which trace appears on the CRO. Outputs are ideal-model values.

## Backend demo contract

Create a separate session using:

```json
{"experiment_id":"dsb-sc-trainer","language":"en","mode":"experiment_demo"}
```

The default mode remains `guided_preparation` for existing API clients. The
DSB-SC pack's authored `demo` profile presets virtual power, a 1000 Hz message,
a 82500 Hz carrier, and auto trigger. It omits inspection and these setup steps;
it never auto-completes a connection or measurement. Nine student-owned actions
remain: six leads, null adjustment and two measurements.

The public session reports `prerequisite_policy: assumed_for_demo`. No concept
checks are marked passed. Evidence uses `virtual_experiment_demo`; the last
measurement transitions to `experiment_complete`, without faults/viva/quiz
screens. Fetch the result from:

`GET /v1/physical-labs/sessions/{id}/experiment-result`

The result explicitly reports `theory_assessed: false` and physical execution
not performed. A demo cannot obtain a regular preparation receipt. Normal-mode
sessions retain orientation, concept checks, demonstration, rehearsal, faults and
readiness assessment. Mode is bound to the creation idempotency key and pinned
pack. Demo and normal preview sessions use separate browser storage references.

## Verified locally

Native Chrome: started directly at the first connection, entered fullscreen,
rejected a wrong lead without advancing, completed all nine steps, observed
1000 Hz and 0.5 V peak at recovery, inspected the actual CRO waveform in
fullscreen, and exited fullscreen. No model providers or screen analysis ran.

Automated: 222 Python tests run, 35 conditional skips, no failures; seven JS
checks cover queued actions, model picking/rendering, guide collision/bounds and
CRO trace selection. Contracts, asset regeneration and pinned-source checks pass.

---

# Physical lab preparation: backend and Kiki integration

## Run and inspect

From the backend root, use Python 3.12 and the existing requirements:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r prototypes/screen_capture/requirements.txt
.venv/bin/python -B -m prototypes.backend --port 8771 --data-dir work/physical-preview
```

In local cookie mode, first visit `http://127.0.0.1:8771/` to establish the existing
owner cookie. Then open `http://127.0.0.1:8771/v1/physical-labs/preview` and choose
Start experiment (or Start preparation in `?mode=preparation`). Resume restores the browser's session reference;
the database owns actual progress. The preview uses no CDN, microphone, screen
capture or provider. It renders the glTF meshes through a portable 3D canvas viewer, including printed circuit artwork, direct part picking and orbit controls.
Rotate by dragging, zoom by scrolling, and select parts directly on the apparatus or through accessible markers. Select a dial to open its slider/numeric setting. During wiring rehearsal, select an output then an input to attach a lead.

Do not use a production cookie to bypass the trusted proxy. Hosted use must retain
the existing `x-kiki-proxy-key` and `x-kiki-owner` server-to-server boundary; those
headers must never be exposed to the browser. Hosting was not changed here.

## Frontend calls

All routes begin `/v1/physical-labs`:

| Method/path | Purpose |
|---|---|
| GET `/experiments` | Prescribed experiment catalogue; includes equipment/review labels |
| GET `/experiments/{id}` | Public pack with questions but no solutions |
| GET `/assets/{name}` | Authenticated glTF asset with embedded buffers |
| POST `/sessions` | Create/resume an idempotent owner-scoped preparation |
| GET `/sessions` | Recent owner sessions |
| GET `/sessions/{id}` | Current stage, apparatus, evidence, activity and revision |
| GET `/sessions/{id}/pack` | Public projection of the session's pinned pack |
| POST `/sessions/{id}/events` | Validate a student action and return saved state |
| GET `/sessions/{id}/observations` | Virtual readings, model assumptions and trace arrays |
| GET `/sessions/{id}/receipt` | Prepared receipt and college revision card; 409 until complete |
| GET `/sessions/{id}/experiment-result` | Completed demo result; separate from preparation readiness |

Creation requires `Idempotency-Key` and same-origin mutation headers:

```json
{"experiment_id":"dsb-sc-trainer","language":"or"}
```

An event includes a unique client ID and the revision last received:

```json
{
  "event_id":"student-action-17",
  "revision":17,
  "kind":"connect",
  "target":"source.message",
  "other":"modulator.message"
}
```

Retry a lost response with the **same event ID and identical body**. A different
event at a stale revision returns 409; reload session state and let the student
act from that state. Never blindly rebase an old action onto a new revision.
Creation retries return current state; event retries return the original event
response. Read the session after reconnection to obtain its latest revision.

Other event kinds: `select`, `advance`, `answer`, `set`, `measure`, `language`.
Answers use `target` = concept ID, fault ID or `readiness`, and an `answers` map
from question ID to option ID. Numeric actions include the specified unit.
Orientation is optional before prerequisites: the Prerequisites button opens the lessons directly, without an all-parts click gate. Required concept checks precede
guided demonstration/rehearsal. No software connection or screen share is needed.

The current step carries instruction, reason and semantic target. Demonstration
steps include a rule for ghost guidance; they do not operate on the student's
independent apparatus. Use the selected language for explanations. English
technical labels remain stable. Question text is currently English; the Odia
apparatus/concept/procedure explanations are machine drafts. Full bilingual
question localisation, reviewed pronunciation and narration are follow-up work.

Kiki web still needs a physical-preparation route, a proxy forwarding these new
paths, a glTF player (or the existing preview renderer), and state/evidence UI.
This branch provides the backend contract and test harness; it does not claim
that the production Kiki UI or hosted cloud engine already includes the feature.

## Existing Kiki UI integration acceptance

1. Add a physical-experiment entry inside the existing Lab mode using the confirmed
   college experiment/equipment association. Open `dsb-sc-trainer` directly for
   this demo; no recognition or uncertain-equipment branch is needed.
2. Extend the authenticated server proxy to cover the catalogue, sessions, events,
   observations, results and versioned assets above. Preserve `Idempotency-Key`,
   origin checks and HTTP status codes. Keep owner identity and proxy credentials
   server-side. Verify against the unified FastAPI deployment rather than assuming
   the existing Worker/D1 lab runtime implements these routes.
3. Create with `mode: experiment_demo` explicitly. Keep `guided_preparation` as a
   separate entry when theory checks are wanted; save/resume session references
   separately by mode. Load the session's pinned pack, not the latest catalogue
   pack, when restoring progress.
4. Reuse or port `apparatus-viewer.mjs`, `component-hints.mjs` and the serialized
   `preparation-client.mjs` into the existing UI. Retain semantic part IDs for
   picking and patch leads. Mount the movable guide and hover tooltip inside the
   fullscreen workspace. Guide endpoints show names only; numbered markers and
   cursor-adjacent hover labels help students locate components themselves.
5. Render the returned activity and feedback after each saved action. Advance only
   when the backend returns the next step. Wire the plots and CRO to the returned
   observation traces; preserve wrong-lead feedback, stale-revision recovery and
   retry semantics. Hover/focus must not submit actions.
6. Accept the integrated flow only after testing all nine actions, rejected leads,
   reload/resume, owner isolation, fullscreen and hover labels. Show the completed
   demo result as virtual experiment practice with theory unassessed. The normal
   preparation flow must still require its prerequisite checks and assessment.

Deployment constraint: the new store is single-instance SQLite under the existing
data directory. Use a persistent volume and one application instance; distributed
storage and multi-instance coordination are separate work. This PR prepares the
backend and reference experience; the Kiki UI rollout is the dependent slice.

## Add another experiment

1. Author a `physical-lab-pack/v1` JSON under `prototypes/physical_labs/packs/`.
2. Define exact equipment, source provenance, review state, semantic parts and
   positions in metres. Use a new versioned asset name.
3. Define ordered prerequisite concepts (five questions per concept), controls,
   allowed connections, ordered steps, measurement tolerances, faults and readiness.
4. Use `declarative/v1` for direct action/measurement checkpoints, or register
   a numerical adapter in `behavior.py` for new experiment physics. Adapters
   implement `observations(pack, apparatus)` and
   `expected_measurement(pack, apparatus, rule)`; the latter validates whether
   the apparatus is ready to measure and returns the expected virtual reading.
5. Run the asset builder, pack/session tests and technical/language review.
6. Associate the pack ID with the college's real curriculum in the application
   catalogue. No recognition or uncertain-match flow is introduced.

The existing action vocabulary supports selection, connections, control settings
and measurements. Positioning can use numeric controls. Experiments needing new
interaction semantics add a contract version/adapter; arbitrary physics is not
automatically generated. The test-only optical geometry pack proves a second
set of target IDs and interleaved reposition/measurement actions can use the
same orchestrator without reordering its procedure.

## Verification

```sh
.venv/bin/python -B -m unittest discover -s tests -p test_physical_labs.py -v
.venv/bin/python -B scripts/smoke-physical-labs.py
.venv/bin/python -B scripts/build-physical-lab-assets.py --check
.venv/bin/python -B scripts/export-physical-lab-contracts.py --check
node --input-type=module --check < prototypes/physical_labs/static/preview.js
node --test tests/test_physical_lab_preview.mjs
.venv/bin/python -B scripts/verify-context.py
.venv/bin/python -B bb8/adapters/reference/bb8.py validate
.venv/bin/python -B bb8/adapters/discovery/sync.py --check
```

The smoke script reads authoring answer keys only for synthetic developer
acceptance. It does not expose a solve endpoint. Do not treat its receipt as
student evidence. The source snapshot, previous screen-reading trial budget and
existing software-lab data are unchanged.
