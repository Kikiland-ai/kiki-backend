# Reader handshakes are idempotent within one stream and document

18 October 2026. Backend repository owns the extension worker/content bridge and its
canonical build. Mac's earlier trial reported `stale_stream_or_generation` and recovered
after Stop sharing -> Check Kiki extension; its detailed lifecycle receipt was not supplied.

## Reproduced mechanisms and fix

The worker previously incremented generation on every hello. The web publisher can send
overlapping hellos at mount, extension announcement and manual recheck. An already
acknowledged publisher then sends snapshots with its former generation and is rejected.
Each page publisher also restarts bridge request IDs at 1. During replacement mounts,
the content bridge broadcast an earlier publisher's response to a later publisher's
waiter with the same ID. Both mechanisms are reproducible in the actual scripts.

The worker now reuses a generation for the same tab/document/stream. A new stream,
document or controlling tab still advances it. All subsequent reader operations check
the current document, and identity-bearing control messages check stream/generation.
The content bridge fences responses by active publisher and hello epoch, supplies
control identity for existing clients and includes stream identity in replies. Late
responses from abandoned publishers cannot resolve a replacement's waiters.

The backend's native reader now carries explicit identity on requests/bye and ignores
other publishers' replies. It ignores commands while superseded. The web consumer can
adopt those additive identity fields too; its existing publisher passes the compatibility
regression and full local React/API/capture browser case without source changes.

Extension version is 0.1.1. Keep sender/origin/frame restrictions, target capture handles,
stale-stream rejection, high-water ordering and redaction. This does not automatically
reclaim control from another tab; explicit recheck remains a deliberate takeover action.

## Evidence and limits

Eight lifecycle regressions cover duplicate hello, stream/document replacement, late
identity-bearing controls, another tab taking over, persisted worker state after
suspension, foreign senders, overlapping bridge IDs and old snapshot responses. One uses
the actual web TypeScript publisher/projector in a deterministic window/Chrome harness.
Before the fix six deterministic extension checks failed; sender-validation passed.

L0 projection/receiver/lifecycle checks: 22/22. Browser window harness: 43/43. Native
capture L2: 31/31, including a real duplicate-hello recovery, target reload, worker stop,
pause/resume, masking and positive/negative canary controls. The React -> API -> candidate
Python -> canonical dev extension case passed in 31.7 seconds against a scratch PR #9
web export, fake identity/Firestore/analyzer and test-only upstream port 8102. No live
provider requests or production learner records were used. Initial harness attempts
collided with the real :8100 backend; only the scratch harness port was changed. One
resume assertion failed in an earlier browser run; an instrumented repeat passed without
an application change. A delayed-final-GET diagnostic then reproduced a separate web
commandBusy race: the window enables Resume while the page is finishing Pause, and the
page rejects it as busy. A serialized command queue with capture-generation fencing was
proposed and verified only in the scratch web export: delayed-response browser regression
passes in 11.2 seconds, and ten capture unit tests pass including Stop fencing a queued
Resume. MAC-WEB-COMMAND-QUEUE.patch contains the proposal for Mac review/adoption. The
primary web checkout remains unchanged. The Mac must retest rapid page/window commands.

These mechanisms fit the earlier symptom but cannot reconstruct its exact historical
event ordering. Connected Mac acceptance is still required with extension 0.1.1 and
the actual candidate runtime receipt. Retain sanitized generations, rejection reason,
command transitions and displayed revision if it recurs; never save screen pixels,
tokens or learner text for this diagnostic.
