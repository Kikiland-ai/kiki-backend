# Atomic local lab creation and replay receipts

18 October 2026. Implements the crash-window finding from the two-repository review.

## Problem and decision

PR #7 first committed a lab and its initial journal event to `labs.sqlite`, then committed
the owner/key/body-bound receipt to `lab-idempotency.sqlite`. A failure between those
commits left a lab without a receipt. Retrying could create a second lab.

Store the receipt in `labs.sqlite` alongside the lab and journal. In the composition
layer, `LabCreateKeys.start()` opens `BEGIN IMMEDIATE`, looks up the owner/key, and either
returns the existing lab or creates the lab, first event and receipt in one transaction.
The original store's RLock serializes connection use; SQLite serializes writers across
independent connections. A small delegating store intercepts only keyed creation so the
frozen domain service and store remain byte-identical. The adapter must insert the first
two rows itself: the original store's connection context would commit before the receipt.

The transaction commits before the route produces its HTTP response. Failure before
commit rolls back all three rows. Loss of the response after commit leaves the receipt
available for retry. Existing HTTP status/header, owner isolation, body conflict and
optional-header behavior remain unchanged. Deleted labs retain replay tombstones and
return 404 on replay rather than being recreated.

## Existing data and rollout

Stop the old backend before upgrading; do not mix old and new writers against one data
directory. Take a consistent backup of both databases and their SQLite-managed state.
Startup copies legacy receipts into the new table using a read-only connection to the
old file. Repeated imports compare exact identities, preserve deleted-lab receipts and
fail closed on conflicts. The old file is retained; no learner records are removed.

This migration cannot reconstruct an old lab whose receipt was never written. Do not
guess identity from model names or delete possible learner labs. Any historical orphan
needs separate evidence and explicit handling.

A code-only downgrade to PR #7 is unsafe after new requests have been accepted: the old
binary cannot see receipts added only to `labs.sqlite`. Stop writers and restore the
consistent pre-upgrade backup if rolling back, accounting for any post-backup work; prefer
a forward fix. No upgrade or rollback has been performed on the running integration data.

## Verification and limits

Ten new offline tests cover an exception after receipt insertion, failure during response
projection, competing connections, owner/body/deletion semantics, legacy import/repeat/
conflict/tombstones, real abrupt process exits before/after receipt and after commit, and
the authenticated HTTP failure -> restart -> retry path. All 149 root tests pass with
the actual local web bridge enabled. Source and frozen-baseline checks pass.

This closes local SQLite creation atomicity. It does not provide shared capture sessions,
cross-worker live state or durable Cloud Run storage. Deploying multiple application
workers remains outside the current prototype's guarantees. Firestore/shared state and
service authentication remain separate deployment prerequisites.
