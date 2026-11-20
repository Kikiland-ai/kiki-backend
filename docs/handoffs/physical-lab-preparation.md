# Physical labs: backend contract and frontend ownership

The student-facing experience belongs to [kiki-web](https://github.com/Kikiland-ai/kiki-web/tree/codex/physical-lab-ui), following its existing Lab mode structure. The earlier backend-hosted preview has been removed. Backend PR #14 supplies the reusable experiment pipeline and DSB-SC content; the companion web branch supplies React screens, rendering, hover hints, the floating guide, fullscreen and the authenticated web API relay.

## Responsibilities

| Repository | Owns |
|---|---|
| kiki-backend | Versioned experiment/equipment packs and apparatus assets, prerequisites, procedure/rule validation, durable owner-scoped state, observations/physics, faults, assessment and results |
| kiki-web | Existing Lab navigation and React screens, service adapters, canvas rendering/picking, leads/markers, cursor hints, movable guide, fullscreen, plots and authenticated Firebase-to-upstream relay |

Versioned glTF content remains with its experiment pack so saved sessions keep the exact equipment model. Rendering code and all student interaction are frontend-owned. Adding an experiment requires authored content/assets and an appropriate behavior adapter; arbitrary new physics is not generated automatically.

## Modes

Create with an `Idempotency-Key` and one of:

```json
{"experiment_id":"dsb-sc-trainer","language":"en","mode":"experiment_demo"}
```

```json
{"experiment_id":"dsb-sc-trainer","language":"or","mode":"guided_preparation"}
```

The default API mode is `guided_preparation`: orientation → prerequisite checks → demonstration → independent procedure/observations → faults → assessment → prepared receipt. Five questions per prerequisite concept remain mandatory before independent practice. Opening prerequisites does not require clicking every apparatus part.

The demo assumes theory knowledge, presets virtual power, a 1000 Hz message, an 82500 Hz carrier and trigger, and starts at the first lead. It contains six leads, null adjustment and two measurements. No connection or measurement is auto-completed. Its terminal state is `experiment_complete`, with a separate result, theory unassessed and physical execution not performed. It cannot earn a regular preparation receipt.

## Routes

All backend routes begin `/v1/physical-labs`. The existing Kiki web API relays the allowlisted subset under `/physical-labs`, authenticating Firebase and deriving the upstream owner on the server.

| Method/path | Purpose |
|---|---|
| GET `/experiments`, `/experiments/{id}` | Confirmed catalogue and public authored pack |
| GET `/assets/{name}` | Versioned embedded glTF; authenticated |
| POST `/sessions` | Idempotent owner-scoped creation; explicit mode |
| GET `/sessions` | Recent owner sessions, including mode |
| GET `/sessions/{id}` | Current stage, apparatus, evidence, activity and revision |
| GET `/sessions/{id}/pack` | Session's pinned public pack; no answer keys |
| POST `/sessions/{id}/events` | Validate student action and return saved state |
| GET `/sessions/{id}/observations` | Ideal-model readings, assumptions and trace arrays |
| GET `/sessions/{id}/experiment-result` | Completed demo result |
| GET `/sessions/{id}/receipt` | Normal preparation receipt; 409 until earned |

Events contain a unique `event_id`, last received `revision`, `kind` and rule-specific fields:

```json
{"event_id":"student-action-17","revision":17,"kind":"connect","target":"source.message","other":"modulator.message"}
```

After losing a response, retry the same event ID with the identical body. A stale different action returns 409: reload and let the student act again; do not silently rebase. Creation retries return current state; event retries return their original saved response. Refresh state after reconnecting. The frontend serializes student actions and drives advancement from returned backend state.

## Run the engine

Python 3.12 and `prototypes/screen_capture/requirements.txt` are required. Start the unified FastAPI backend with a persistent data directory; configure Kiki web's existing trusted lab upstream to point at this instance. Retain the server-only `x-kiki-proxy-key` and `x-kiki-owner` boundary. Enable the physical relay explicitly in the web API. No production origin or rollout is implied by the branch.

The new database is single-instance SQLite (`physical-labs.sqlite`) under the data directory. Use one application instance and a persistent volume. Distributed storage is follow-up work. Existing lab capture/Simulink guidance remains separate.

## Validation and review

Run the physical-lab Python tests, `scripts/smoke-physical-labs.py`, contract exporter `--check`, and asset builder `--check` in this repo. Frontend renderer/interaction tests now run in kiki-web. Asset generation is reproducible; retained v1/v2/v3 apparatus assets protect older pinned sessions.

ANITS is the instructional source; real trainer photographs informed the original model. Numerical outputs are an ideal coherent DSB-SC model (unity receiver gain yields 0.5 V recovered peak). Qualified technical and native Odia review remain pending. Prepared virtual evidence does not certify physical handling or practical proficiency.
