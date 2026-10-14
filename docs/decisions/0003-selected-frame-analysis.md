# Selected-frame analysis on the private hosted receiver

Date: 13 October 2026 · Status: implemented, locally verified and privately published; exact publication recorded in active.md

## Authority and scope

The user confirmed that actual screen sharing works, then requested starting frame analysis and explicitly approved reusing the environment's existing Gemini key as a server-side Site secret. This authorizes the bounded analyzer and updating the existing private Site. The broader backend remains separate; no kiki-backend commit or push is implied. BB8 engineering implementation/debugging and prompt-design were applied in reference mode.

At this initial trial the FastAPI receiver was receipt-only. The subsequent [Python continuation](0004-python-lab-analysis-and-progress.md) now implements local lab analysis/progress as the user explicitly requested; it has not replaced the hosted Worker. The separately hosted adapter was necessary because this interface exposes no verified HTTPS port-preview control. It keeps the existing private audience and lives at https://kiki-screen-receiver.woodsycarp256.chatgpt.site. Its source is the Site's repository, checked out at /workspace/sites/kiki-screen-receiver; exact source/version/deployment records belong in active.md.

## Implemented loop and endpoint

1. The browser obtains a native getDisplayMedia stream for a user-selected tab/window/screen, with no audio. It extracts bounded JPEGs and uploads them via HTTPS POST /screen-sessions/{id}/frame. The upload loop waits two seconds after an upload completes, so its rate is at most 0.5 Hz. This is sampled-image transport, not a WebRTC server or video recording.
2. After the receiver returns the actual admitted JPEG, the browser may independently POST those exact bytes plus their frame metadata to /screen-sessions/{id}/analyze. The signed capture receipt must match hash, sequence and metadata before a model call is admitted.
3. Gemini sees one current image and the previous observation REPORT as text, not a prior image or full recording. The prompt restricts output to visible summary/facts, a reported-state comparison and uncertainties; embedded screenshot text is untrusted data. Runtime validation rejects extra fields, malformed/truncated output and oversize text. It cannot prove visual truth.
4. The runtime supplies provenance rather than trusting model-generated IDs/times: analysis ID, frame ID, SHA-256, capture elapsed time, receipt/completion time, model and prompt version. Each fact resolves to the source-frame ID.
5. The browser renders descriptions and exposes the JSON. GET /screen-sessions/{id}/observation combines the latest signed capture and analysis receipts. Separate cookies prevent a late analysis response from replacing a newer capture receipt. The page also merges results by completion time while preserving the current frame/count/lifecycle.

Capture and analysis run independently. No accumulated frame queue or automatic retry is used inside the provider request. A slow call simply means more frames arrive before its result. Provider/schema/network failures preserve the prior good report, expose the error and leave sharing active. Pause stops new sampling and analysis; an existing analysis can finish. Stop aborts the browser's analysis request and ignores its late result, but cannot guarantee cancellation of work already accepted by Gemini.

## Runtime output

After a successful interpretation, schema is screen-awareness/v1. Before success it remains screen-receiver/v1 with frame_receipt mode and null summary. The observation includes:

```json
{
  "mode": "vision_observation",
  "analysis_status": "available",
  "summary": "Oscillator controls are visible.",
  "facts": [{"id": "session:analysis:1:fact:1", "description": "Control voltage reads -0.5 V.", "evidence_frame_id": "session:1:1"}],
  "changes": [],
  "uncertainties": [],
  "source_frame": {
    "frame_id": "session:1:1",
    "sha256": "runtime hash of the analyzed JPEG",
    "sequence": 1,
    "captured_elapsed_ms": 100,
    "server_received_at": "runtime UTC timestamp",
    "server_received_unix_ms": 1791914400100
  },
  "latest_frame": {"frame_id": "session:1:4", "sequence": 4},
  "analysis_id": "session:analysis:1",
  "completed_at": "runtime UTC timestamp",
  "completed_unix_ms": 1791914406500,
  "model": "gemini-3.1-flash-lite",
  "prompt_version": "screen-observer/v1"
}
```

This abbreviated example explains the mapping; actual frame metadata contains geometry, byte count and chronology. source_frame is the actual model input; latest_frame may be newer. Top-level analysis.age_ms measures source-frame receipt age, stale becomes true above 20 seconds, and capture freshness is computed separately. A changes item labels its basis current_frame_vs_previous_report and references both frames. These are sampled descriptions, not verified student actions, scientific correctness, checkpoints or mastery evidence.

## Budgets, storage and secret handling

- Default model gemini-3.1-flash-lite, minimal thinking, bounded structured JSON and a 20-second provider timeout. The browser's request timeout is 25 seconds. Normal UI behavior allows one browser request at a time, at least ten seconds between starts, and 30 starts per share session including failed browser requests. When that limit is reached, only analysis stops; capture can continue to its existing 30-minute limit. Server signed receipts add cooperative per-session admission checks.
- Signed-cookie limits are not durable global quota/concurrency controls: cookie replay/forks and abandoned provider calls require a future shared coordinator. Aborting a browser request does not establish that its provider cost was avoided. No production billing ceiling is claimed.
- GEMINI_API_KEY and CAPTURE_RECEIPT_KEY are secret Site runtime variables. No key is in browser code, source, archive or documentation. The user explicitly approved the existing-key transfer; only server code uses it.
- There is no D1/R2 image archive or durable hosted observation journal. The browser keeps bounded receipt/observation metadata in page memory; signed cookies retain the current bounded state. Closing/restarting the page loses that in-memory history. Past hashes cannot reconstruct pixels. Provider processing/retention is separate from the receiver's no-image-archive policy.
- All candidate frames still cross the network, even when unchanged. At 0.5 Hz there are up to 1,800 candidates/hour; independent analysis admission and zero receiver image retention already prevent one model call/object write per candidate. Adaptive change filtering, legibility checks, selected-input evidence retention and durable history are next optimizations. Raw selected evidence is required before claiming replayable/auditable visual findings.

## Verification and limits

Fourteen Worker tests passed, covering strict model output, matching pixel provenance, late response/capture state separation, provider failure preserving prior results, duplicate-frame rejection, interval/trial limits and continued capture after analysis limits. Native Chromium capture with an explicit slow/failing local provider fixture passed with ten received frames, late-result preservation, provider 503 isolation, pause/resume/stop and no JavaScript errors. This browser mock proves isolation, not model accuracy.

Two real Gemini structured image calls on controlled browser-rendered screenshots passed the exact output validator. First: Paused, -0.5 V, 950 Hz (6.52 seconds). Second: Running, 0.5 V, 1050 Hz (11.57 seconds), with a correct comparison against the earlier report. No clicks were inferred. These examples establish this bounded provider path, not general screen-reading accuracy or actual Simulink behavior. Two gemini-3.5-flash-lite image calls timed out at 30/45 seconds; a gemini-2.5-flash-lite probe returned eligibility 404. The working 3.1 model was selected without changing the unrelated audio/text pipeline.

The owner's real hosted share already worked for receipt mode; post-publication analysis of their screen remains an acceptance check. A labeled persistent-state/small-text/uncertainty evaluation, surface-switch epochs, restart recovery, durable history/evidence and global budgets remain next. Instructional planning and drawing overlays remain separate proofs.
