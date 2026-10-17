# kiki-web's API fronts lab execution

18 October 2026. User decision for moving screen sharing into kiki-web Lab mode ([handoff](../handoffs/kiki-web-lab-mode-screen-share.md)).

## Decision

The browser talks only to kiki-web's `apps/api`, which:

1. verifies the Firebase ID token (`verify_id_token(check_revoked=True)`, Google provider);
2. checks enrollment and that the user owns the `prep-*` lab preparation;
3. forwards a fixed allowlist of lab-execution requests to kiki-backend's Python service, as its trusted upstream.

The forwarded requests carry `x-kiki-owner: fb:<uid>` and the server-only `x-kiki-proxy-key`, with `Origin` rewritten to the upstream origin. kiki-backend keeps screen reading, tracker state and analysis; kiki-web keeps identity, enrollment, preparation and the student UI.

The link between the two is one Firestore document per preparation: `learners/{uid}/labExecutions/{prepId}`, holding the upstream `backendLabId`.

## Why

- It keeps kiki-web's contract rule: all data goes through one API, and the backend derives the UID from the token.
- It reuses the lab preparation record kiki-web already creates in Firestore, so the session the student opens at `/labs/:sessionId` is the one that gets executed.
- kiki-backend already enforces this boundary through `SiteProxyGuard` (HTTP and WebSocket, constant-time key check, owner required), with tests. No new auth scheme is needed there.
- The browser never holds a backend secret or model key.

## Consequences

- kiki-web's API needs a streaming-capable upstream client: SSE passthrough for `check-stream`, and a WebSocket relay for frames.
- Browser WebSockets cannot send `Authorization`, so frames use a short-lived, single-use ticket.
- Both services need hosting before production (blockers B1 and B2 in the handoff). Development runs locally: `127.0.0.1:5174` → `:8000` → `:8100`.
- The demo reader Worker is not part of this path; it stays a backend QA tool.

## Also decided

- kiki-web work starts from `main`.
- Commits are made as `arpanvihan5-sketch`, overriding kiki-web `AGENTS.md:7` for this work.
- kiki-web's production web address is a high-priority blocker.
