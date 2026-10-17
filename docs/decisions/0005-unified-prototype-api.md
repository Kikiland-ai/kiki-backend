# 0005 — Compose screen/lab and mixed-language APIs in FastAPI

14 October 2026. Accepted for local prototype implementation; hosting remains pending.

The user asked to document the stable screen-reader, then verify and connect mixed-language text/audio endpoints before setting up latency experiments. The prior text/speech implementation had library/CLI adapters and a design assessment, but no HTTP routes. Screen/lab already had FastAPI routes; the user-tested Site still ran Worker/D1.

Add a composition entry point, preserving the frozen screen/lab implementation. Mount owner-scoped prepared-source mixed-language jobs, durable SQLite admission/stage checkpoints, explicit retry/cancel and separate text/audio retrieval. Execute blocking legacy providers in a bounded dedicated executor. Expose route-derived OpenAPI and a frontend handoff; never call fixture execution a live provider test. Keep the original CLI unchanged.

This is one single-process prototype, not the proposed distributed actor system. Interrupted work needs explicit retry; completed translation/text is reused. Inputs/idempotency bind to owner/source/profile/audio; no arbitrary provider setting is accepted from the browser. Text/audio cannot alter lab evidence. Artifact alignment and domain/native-language review stay pending. Text/TTS single-key policy remains distinct from screen key rotation; shared quota scheduling is unresolved.

The Site edge must forward Idempotency-Key. Prepare a separate edge helper for future rollout rather than changing/redeploying the frozen working Site. The consolidated container starts prototypes.backend; a real Python origin, persistent volume and authenticated HTTP/WS/media checks are still required before giving the frontend a live base URL.

See [frontend API handoff](../handoffs/frontend-api.md), [screen baseline](../baselines/screen-reader-v1.md), and the historical [architecture assessment](../architecture/mixed-language-fastapi.md). The latter's distributed queue/store/media plans remain later work; this decision implements only the bounded coherent API slice. No model/streaming experiment was executed and no production Site was changed.
