# Coordination: analysis-owned drawing experiment

15 October 2026. Prepared at the user's request for the reader session:
`codex://threads/01a135c7-476f-70c3-bd7e-9c109051706e?hostId=durable`.
That link identifies the receiving chat; this document does not claim that chat
has been read or messaged. The user can paste the brief below into it.

## Branch separation

All three new branches start from the same coordination-only commit based on
`experiment/stream-context-batch` at
`ae234dcdd78b91ef7d6e6b528b14f2e9196808bb`. The common commit adds documentation
and the branch registry; it changes no application runtime.

| Branch | Owner | Work |
| --- | --- | --- |
| `experiment/analysis-owned-guidance-producer` | Reader/latency chat | Model input/output schema, strict Python/Worker parsing, action/context admission and early committed drawing payload |
| `experiment/analysis-owned-guidance-renderer` | Writer chat (this session) | Extension, deterministic consumer, transforms, presentation lifetime, cancellation and actual paint ACK |
| `integration/analysis-owned-guidance` | Writer chat, integration only | Combine reviewed producer/renderer commits and wire shared hosted client/build/routes; run the end-to-end gate |

Keep `experiment/stream-context-batch` as the latency control and leave its draft
baseline promotion PR (#1) scoped to reader improvements. Neither new experiment
branch targets baseline. Do not merge this drawing experiment into that PR.

Preserve `baseline/screen-reader-v1`, `baseline/screen-writer-v1`, existing Sites,
private audiences, secrets and saved learner runs. The older local
`integration/screen-writing-v1` at `1acbcc65781223c7a61a7a4bc3978e5a0230cfd1`
retains earlier writer work and local delivery fixes; it is a donor/reference,
not the new experiment base. Do not merge its entire legacy hosted-reader tree
into the new branches: the active latency Site lives in
`prototypes/json_stream_site`, and frozen baseline source hashes must stay intact.

## Ownership of files and shared integration points

Producer owns `prototypes/json_stream/` model/stream components, hosted
`prototypes/json_stream_site/worker/{analysis,stream,stream-core}.js`, a new
versioned analysis/drawing schema with examples, and producer regression tests.
It also owns the committed projection and producer-generated ordered cancellation.
Do not change `contracts/screen_writing.schema.json` v0.2 or its catalog in place.

Renderer owns `prototypes/screen_writing/shared_tab/`, new isolated consumer/
protocol assets, and rendering/delivery tests. It consumes the published
producer schema. It does not interpret raw criterion findings, choose teaching
actions or generate new instructional text.

Shared `prototypes/json_stream_site/assets/lab.js`, build scripts, Worker routes
and generated `worker/index.js` are integrated on the integration branch. Neither
side should independently rewrite these hot spots. Publish the producer export
and consumer entrypoint with examples first; integration wires the single committed
handoff once. Keep owner-specific implementation notes in distinct files instead
of competing edits to `docs/plans/active.md`; reconcile that plan at integration.

## Proposed contract boundary

The model receives the exact admitted frame, authored current/eligible actions and
target catalog. In the **same model request** as criteria/action findings, it
returns a bounded typed `screen_guidance` field: action/target IDs, normalized
regions, allowlisted shapes and note references. No second model call is used to
resolve a target or decide what to draw. The exact field/schema/version remains a
proposal until the producer publishes it with fixtures and the renderer accepts it.

For the practical lab, canonical instructions/settings remain tracker-owned.
Notes reference that authored text. The server mechanically validates/adapts the
candidate for the **resulting committed current action**, attaches trusted source
frame/context/sequence/expiry and emits it with `guidance_committed`. Provisional
findings never draw. No matching current-action candidate means no drawing until
the next normal frame; old geometry is never relabelled for an advanced action.

The extension draws the supplied operations, converts normalized frame coordinates
to the verified tab viewport, replaces the full layer and reports actual paint.
Source/context/expiry checks remain required; stale packets discard everything,
including fallback text. Required targets that cannot be resolved allow only
canonical text in valid current context. Paint/ACK never completes a checkpoint
or establishes understanding. The student performs every lab action.

Preserve the branch's batched provider I/O, fresh per-chunk context validation,
short complete decision, provider STOP/full JSON gates and independent committed/
auxiliary delivery. Adding drawing necessarily changes the model output contract;
do not silently append a field to its strict three-field parser. Explicitly
version/negotiate the changed model/stream projection. Keep the payload bounded
and measure its generation/delivery cost instead of promising a latency win.

The producer handoff must propose the chosen Site origin, source binding/frame
transport, authenticated delivery, clock/deadline semantics and version handshake.
No secrets should be pasted into chat. These details are not settled merely by
creating branches. The current extension allowlist does not include the latency
Site origin; that must be reconciled explicitly before live connection.

## First exchange and acceptance

Producer first publishes: schema/version, valid resolved/text-only/no-cue examples,
stale/cancel/action-advancement examples, export location, base/head commit SHA,
exact offline test command and transport/clock proposals. Writer checks those
fixtures against the compositor before either side claims live interoperability.

Offline acceptance must exercise one delayed analysis response while periodic
frames continue, through actual parsing, committed projection, consumer and
compositor, with independently checked target pixels and persisted exposure ACK.
Cover duplicate renders, capture-versus-paint contention, pause/source/view/visit/
parameter changes, missing STOP, late malformed output, unresolved targets,
reordering, cancellation and blocked auxiliary tails. Compare the latency control
with drawing enabled under the same settings; retain slow/failed/discarded cases.
Routine regressions should not require the user to repeat the lab.

Installed extension + native sharing + actual Simulink remains a distinct sampled
integration check. Current legacy component suites pass, but the latest native
controlled full-path attempt stopped at source binding and did not paint. A
viewport smoke test or screenshot preview cannot close that acceptance boundary.

## Paste into the reader chat

> Please coordinate the new **analysis-owned screen-guidance experiment** with
> the writer session. Work only on `experiment/analysis-owned-guidance-producer`.
> All new branches share a documentation-only base over the reader control
> `ae234dcdd78b91ef7d6e6b528b14f2e9196808bb`.
>
> Read `docs/handoffs/analysis-owned-guidance-experiment.md` and
> `docs/decisions/0007-analysis-owned-screen-guidance.md` on that branch. The goal
> is one model response containing findings plus typed drawing intent/geometry,
> delivered with `guidance_committed`; there is no second model reasoning call.
> You own the producer schema, strict Python/Worker parsers, current-action
> admission and early committed payload. Publish the proposed versioned schema
> and examples first, with your commit SHA and transport/clock assumptions.
>
> The writer owns `experiment/analysis-owned-guidance-renderer`; integration is
> `integration/analysis-owned-guidance`. Keep the latency control branch, both
> baselines, draft PR #1 and existing deployed Sites unchanged. Shared client/
> build/routes are wired on the integration branch after the interface is agreed.
> Canonical lab instructions/progress remain tracker-owned. The extension renders
> deterministically, with source/context/expiry/cancellation checks and a real
> paint ACK. A rendering acknowledgement never completes a checkpoint.
