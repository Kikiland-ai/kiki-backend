## Beginner guidance (14 October 2026)

The twelve stages now use forty ordered instruction actions from procedure.py. Each includes suggested placement, concrete procedure, expected result and inline values. guided.py selects current/next from recent support and historical action progress, never from free-form model instructions. It preserves remembered actions through hidden views/pauses while freshness-gated criteria still own checkpoint completion; expired evidence requests final named checks. The observer prompt is dsb-step-observer/v3 and distinguishes Carrier/Local carrier by identity, with strict validated action findings. See ../../docs/decisions/beginner-lab-guidance.md. The exported policy is screen-guided-policy/v2; the old criterion_actions map is removed. screen-writing/v0.2 remains unchanged.

## Continuous operation (14 October 2026)

The former 30-check, 500-event and 100-response rejection caps are removed. Provider throttling records a durable retry deadline and preserves capture and checkpoint progress. The browser automatically checks the newest fresh frame after the cooldown; it never queues old pixels. The last 100 responses are a prompt/projection window; full responses remain in events. GET events accepts `after`/`limit` (maximum 100 per page); export streams all events through the selected revision. See `docs/decisions/continuous-screen-analysis.md` for key pool configuration and remaining operational boundaries. Historical statements below about those caps are superseded.

# Python DSB-SC observation and checkpoint prototype

The analysis pipeline, progress rules, storage and API now run in Python/FastAPI. Browser JavaScript only captures pixels, calls endpoints and displays server state. The previously published private Site still runs its earlier Worker backend; this local Python implementation has not been deployed behind that Site.

## Current guided mode

The user chose automatic advancement when visible evidence is sufficient. `StartLab.progression_mode=screen_guided` now removes the checklist and enables bounded automatic observation/progression. Default reviewed mode is retained for the earlier explicit-review API/tests. `guided.py` owns the policy and current/next copy; a temporary live Site adapter consumes its export while Python hosting is pending. The shared frontend is verified against both APIs.

Two matching readings from distinct frame IDs can satisfy eligible visible criteria as `completion_basis=screen_inferred`, with unreviewed model evidence. Every criterion must be satisfied before advancing. The resulting done step has `assessment_status=unassessed`; no prerequisite pass, verified grade or mastery is inferred. Saves/workspace identity need explicit confirmation; observations/explanations remain unassessed student reports. This authorized workflow supersedes the earlier requirement for operator review on every prototype step. Reviewed mode retains that requirement.

Recent support can span settings dialogs within one visit/workspace/parameter/condition/capture scope. Mismatches, context changes and 120-second support expiry prevent unsupported advancement. View changes invalidate current geometry without discarding unchanged, recent parameter observations from another dialog. Unchanged pixels skip calls, except for a second match or expiring support; there is no fixed start-count cap. Next copy shows the next pending action inside a checkpoint before the next checkpoint.

Cloud continuation: the user requires browser access without a local repo/install. [The cloud package](../../deploy/fastapi/README.md) now prepares a container and authenticated Site proxy boundary. The private Site's inactive edge adapter has been published; it stays on the earlier backend until an actual Python host is deployed and verified. Render was offered as a supported hosting connection; an unconnected account is not a deployed service.

## Run

From the repository root, with Python 3.12:

```sh
python -m pip install -r prototypes/screen_capture/requirements.txt
python -B -m prototypes.screen_capture --port 8765 --data-dir work/python-lab
```

Configure `GEMINI_API_KEY` through the server environment, never in browser code or a chat message. `GET /health` reports whether it is configured without revealing it. Open http://localhost:8765 on the machine running the server. Remote sharing needs supported authenticated HTTPS hosting that preserves the WebSocket upgrade, cookies and Host/Origin. No cloud preview or Python hosting URL is established by this implementation.

Enter the saved Simulink Online model name, select the builder trial, begin the lab, and select **Share screen**. Choose the matching model. **Check this step** analyses a recently received frame. Review the checked image, select criteria you personally verified, enter a review note, and confirm. Every criterion is required before advancing. You perform all model edits, runs and saves.

Builder mode keeps prerequisites and conceptual understanding unassessed. In reviewed mode a model match is not completion. In screen-guided mode repeated matches can advance inferred progress with an explicit completion basis. Operator reviews and student reports do not become independent simulator verification or mastery. There is no normal learner assessment gate in this prototype.

## Pipeline and files

1. `prototypes/screen_capture/server.py` receives ordered JPEGs through the existing WebSocket at up to 0.5 Hz, checks actual decoded dimensions, and calculates SHA-256. Its latest image is in memory; receipt metadata is in SQLite.
2. `contracts/lab_tracking.py` validates bounded requests/results. `/check` accepts a frame ID and view revision, not arbitrary frame pixels or a client-authored observation. `service.py` retrieves the exact admitted bytes, compares their hash/size, snapshots the checkpoint/visit/workspace/epoch/parameter/condition/view context, and durably consumes an analysis attempt before awaiting the provider.
3. `analysis.py` sends those exact pixels plus authored checkpoint criteria to Gemini. Screenshots and student reports are untrusted data. Output must contain exactly one unique finding per criterion: match, mismatch or unknown. Runtime shape validation does not establish scientific or visual correctness. Model/prompt identifiers and frame provenance come from the server.
4. `service.py` rechecks revision, lifecycle and frame age after the await. A result for a changed visit/view/condition/parameter context cannot become the current observation. Newer receipt frames do not rewrite the frozen analysis input. Provider failures retain a previous usable candidate and record a failure; a context change invalidates it.
5. Explicit `/review` attaches evidence to criterion IDs and the original context. Partial reviews stay on the step. The last satisfied criterion completes the step exactly once and starts a new visit at the next checkpoint. No analysis, rendering or delivery acknowledgement completes a checkpoint.
6. `store.py` atomically saves a SQLite projection and an append-only event under a compare-and-swap revision. Student predictions, observations, explanations, questions and notes retain visit/concept IDs and optional self-confidence separately from assessed understanding. Wall, tracking, paused, disconnected and fresh-observation time remain neutral telemetry.

The twelve authored checkpoints come from `docs/architecture/examples/dsb-sc.demo-definition.json`, pinned to Design-Thinking commit `2a6c843448d81062f89596b941516f8b7817ec79`. CP-11 review requires `phase_fault`; CP-12 requires `restored_baseline`. Declaring a condition does not change the physical model. Conditions and parameter changes invalidate current partial criteria but preserve historical evidence. Revisits preserve historical visit/evidence records and reset the current/downstream queue.

## API

All lab routes require the local HTTP-only owner cookie. Writes require the same Origin/Host. Example JSON bodies below are field shapes, not user evidence.

| Endpoint | Request/result |
| --- | --- |
| GET /lab-definition | Pinned authored experiment |
| POST /lab-sessions | `{model_name, operator_trial:true}`; creates owned run |
| GET /lab-sessions | Owned run summaries |
| GET /lab-sessions/{id} | Current JSON observation, now/next, queue and reviewed evidence |
| POST /lab-sessions/{id}/attach | `{revision,capture_session_id}`; new capture epoch, preserved queue |
| POST /lab-sessions/{id}/check | `{revision,frame_id,view_revision}`; admitted analysis and candidate |
| POST /lab-sessions/{id}/review | `{revision,criterion_ids,review_note}`; reviewed criterion progress |
| POST /lab-sessions/{id}/responses | `{revision,kind,text,self_confidence:null}`; typed student report |
| POST /lab-sessions/{id}/context | `{revision,action,...}`; pause/resume/view/parameter/condition/revisit |
| GET /lab-sessions/{id}/image | Latest checked exact JPEG, up to 20 seconds of receipt age |
| GET /lab-sessions/{id}/frame-handles/{handle_id} | Owned ephemeral exact JPEG + base64 JSON X-Frame-Provenance; otherwise 410 |
| GET /lab-sessions/{id}/events | Ordered append-only journal, paginated with after/limit |
| GET /lab-sessions/{id}/export | Definition, current projection and events, excluding owner bearer capability |
| DELETE /lab-sessions/{id} | Delete this owned run and metadata; drop checked pixels |

Context actions are `pause`, `resume`, `view_changed` with increasing `view_revision`, `parameters_changed`, `condition` with an applicable condition, and `revisit` with a current/earlier checkpoint ID. Required body fields and bounds are in the Pydantic models. Mutations for an old revision return 409. Duplicate/foreign criterion IDs and invalid student/model output return 422.

Runtime projections are explicitly `lab-python/v1`: this small prototype uses a checkpoint-keyed `steps` map, typed responses and runtime admission fields. It does not claim wire compatibility with the proposed full `lab-tracking/v1` schema or the earlier Site's `lab-demo/v1`. The published `screen-writing/v0.2` schema remains unchanged. Frame handles/context are now provided by Python; authoritative cue sequencing, ACK journaling and the renderer transport handshake remain separate integration work.

## Limits and retention

- One FastAPI process, four provider slots, one admitted check per lab, at least ten seconds between starts, no fixed start-count cap, provider timeout twenty seconds. Waiting for a slot is included in that timeout. Provider cooldowns trigger automatic fresh-frame retries without accumulating a frame queue.
- Frames must be at most six seconds old at admission; analysis/review pixels at most twenty seconds old. A writer handle expires no later than eight seconds after completion or twenty seconds after receipt. Capture elapsed time is client-monotonic; receipt/admission/completion are server UTC. Receipt age does not prove absence of upstream capture delay; clock calibration remains integration work.
- No run-creation or journal-event cap. Last 100 responses are kept in the state/model-context window; full records persist in the append-only journal. SQLite metadata persists until deletion; no automatic metadata TTL is claimed.
- Only latest received/checked JPEGs are kept in memory. New successful checks replace checked pixels. Pause, capture lifecycle changes, context changes, completion, delete and server restart invalidate/drop them. Expired handles cannot read them. No screenshot/video archive or historical raw image reconstruction exists.
- Capture disconnect/pause/stop is reported directly by the FastAPI WebSocket lifecycle, independently of analysis. Progress persists across new capture segments and process restarts. A restarted process conservatively counts the interval since the last durable timing write as a gap; it never claims continuous observation during that interval.
- Encoded dimension changes and the **View changed** control advance detected view revisions. Generic screen sharing still cannot reliably detect every Simulink pan/scroll/modal change. This is not a proven live-overlay adapter.
- The owner cookie is a local prototype capability, not production account authentication. Use localhost or an authenticated HTTPS host. Session/projection formats and storage are not a production distributed coordinator.

## Verification

```sh
python -B -m unittest discover -s tests -v
python -B scripts/check-lab-tracking-design.py
python -B scripts/check-screen-writing-design.py
```

Fifteen new Python pipeline/API acceptance checks cover a complete twelve-checkpoint run, fault/restoration condition gates and typed response gates, all-match model output remaining unreviewed, partial reviews, duplicate revisions, historical evidence, provider failure/recovery, stale visits/views/parameters, exact immutable pixel provenance, owner isolation, handle/review expiry, timing, pause/disconnect and restart. Existing capture/text/audio checks remain independent.

`scripts/check-python-lab-browser.py` uses native Chromium capture of a controlled source and **requires** an explicitly injected fixture analyzer at `/health`. It verifies checked-image display, review advancement, question journaling, reload/new-capture progress and no JavaScript errors. This is not an actual Simulink run. A separate real Gemini transport check on a controlled blank JPEG returned schema-valid unknown findings; it does not prove Simulink recognition.

Next acceptance is CP-DSB-01 on an actual shared Simulink Online workspace through a reachable Python deployment. Actual overlay rendering remains the parallel session's separate integration test.


Provider routing now uses durable individual-key round robin, immediate 503/transport fallback and at least sixty seconds after a failed full sweep. Configure server secret GEMINI_API_KEYS as a JSON string list or {key,quota_pool} entries; at least two distinct keys are needed to alternate. Same-project 429s share cooldown. Default model: gemini-3.5-flash-lite, with optional GEMINI_LAB_MODEL override. See [rotation and live model comparison](../../docs/decisions/key-rotation-and-model-comparison.md), including the bounded-frame budget and controlled evidence boundary.
