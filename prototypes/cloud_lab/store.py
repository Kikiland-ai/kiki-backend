"""Shared Firestore lab projection and journal; no SQLite or startup mutation.

Pass an explicitly selected named-database client. Documents contain metadata and
JSON domain state, never screen bytes, provider secrets or identity bearer tokens.
Deletion leaves a minimal owner-bound tombstone so old create receipts cannot revive
a deleted lab. Tombstone/receipt retention is deliberate, not a transient frame TTL.
"""

import copy
import hashlib
import json
import time
from contextlib import contextmanager
from contextvars import ContextVar

from fastapi import HTTPException


def run_atomic(client, operation):
    """Use real Firestore retries; an explicit fake hook supports offline tests."""
    if hasattr(client, "_run_transaction"):
        return client._run_transaction(operation)
    from google.cloud import firestore
    return firestore.transactional(operation)(client.transaction())


def encode(value):
    encoded = json.dumps(value, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    # Reserve Firestore's document overhead and avoid opaque provider-size failures.
    if len(encoded.encode("utf-8")) > 900_000:
        raise HTTPException(413, "Lab state is too large; export before starting another run")
    return encoded


class FirestoreLabStore:
    def __init__(self, client, collection_prefix="kiki_cloud", clock=time.time):
        if getattr(client, "_database", None) == "(default)":
            raise ValueError("Cloud labs require an explicit named Firestore database")
        self.client = client
        self.clock = clock
        self.labs = client.collection(collection_prefix + "_labs")
        self.captures = client.collection(collection_prefix + "_captures")
        self.receipts = client.collection(collection_prefix + "_lab_create_receipts")
        self._staged = ContextVar("cloud_lab_staged_create", default=None)

    @staticmethod
    def _owned(snapshot, owner):
        value = snapshot.to_dict() if snapshot.exists else None
        if not value or value.get("owner") != owner or value.get("deleted"):
            raise HTTPException(404, "Lab session not found")
        return value

    def _document(self, lab_id):
        if not isinstance(lab_id, str) or not lab_id or "/" in lab_id:
            raise HTTPException(404, "Lab session not found")
        return self.labs.document(lab_id)

    def load(self, lab_id, owner):
        return json.loads(self._owned(self._document(lab_id).get(), owner)["state_json"])

    def list(self, owner):
        # Single field query avoids deployment dependence on composite indexes.
        states = [json.loads(v["state_json"]) for s in self.labs.where("owner", "==", owner).stream()
                  if (v := s.to_dict()) and not v.get("deleted")]
        return sorted(states, key=lambda v: v.get("runtime", {}).get("last_accounted", 0), reverse=True)[:8]

    def all(self):
        return [json.loads(v["state_json"]) for s in self.labs.stream()
                if (v := s.to_dict()) and not v.get("deleted")]

    def by_capture(self, capture_id):
        return [json.loads(v["state_json"]) for s in self.labs.where("capture_session_id", "==", capture_id).stream()
                if (v := s.to_dict()) and not v.get("deleted")]

    @staticmethod
    def _validate(state, event, expected=None):
        revision = state.get("revision")
        if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
            raise ValueError("Lab revision must be a positive integer")
        if event.get("event_sequence") != revision or not event.get("event_id"):
            raise ValueError("Lab event must match the projection revision")
        if expected is not None and revision != expected + 1:
            raise ValueError("Lab writes must advance exactly one revision")
        if not state.get("owner_id"):
            raise ValueError("Lab writes require an owner")

    def _body(self, state):
        return {"owner": state["owner_id"], "revision": state["revision"], "deleted": False,
                "capture_session_id": state.get("workspace", {}).get("capture_session_id"),
                "updated_at_unix": self.clock(), "state_json": encode(state)}

    @staticmethod
    def _event_ref(ref, event):
        return ref.collection("events").document(f'{event["event_sequence"]:020d}')

    def _write_create(self, transaction, ref, state, event):
        transaction.create(ref, self._body(state))
        transaction.create(self._event_ref(ref, event), {"sequence": event["event_sequence"],
                                                       "event_id": event["event_id"], "body_json": encode(event)})

    @contextmanager
    def stage_create(self):
        """Build the existing domain result before committing a receipt transaction."""
        staged = []
        token = self._staged.set(staged)
        try:
            yield staged
        finally:
            self._staged.reset(token)

    def create(self, state, event):
        self._validate(state, event)
        if state["revision"] != 1:
            raise ValueError("New labs must begin at revision one")
        staged = self._staged.get()
        if staged is not None:
            if staged:
                raise RuntimeError("Only one lab may be staged per creation")
            staged.append((copy.deepcopy(state), copy.deepcopy(event)))
            return
        ref = self._document(state["lab_session_id"])
        def commit(transaction):
            if ref.get(transaction=transaction).exists:
                raise HTTPException(409, "Lab session already exists")
            self._write_create(transaction, ref, state, event)
        run_atomic(self.client, commit)

    def capture_snapshot(self, capture_id, owner):
        """Metadata-only producer snapshot suitable for a guarded lab mutation."""
        snap = self.captures.document(capture_id).get()
        row = snap.to_dict() if snap.exists else None
        if row and row.get("owner") != owner:
            raise HTTPException(404, "Session not found")
        guard = {"capture_id": capture_id, "owner": owner, "exists": bool(row)}
        if not row:
            return {"status": "disconnected", "view_revision": None, "guard": guard}
        guard["fields"] = {key: row.get(key) for key in ("fence", "producer", "status", "lease_until")}
        view = (row.get("latest") or {}).get("view_revision")
        guard["view_revision"] = view
        status = row["status"]
        if status in ("sharing", "paused") and row.get("lease_until", 0) <= self.clock():
            status = "disconnected"
        guard["effective_status"] = status
        return {"status": status, "view_revision": view, "guard": guard}

    def _verify_capture_guard(self, transaction, guard, owner):
        snap = self.captures.document(guard["capture_id"]).get(transaction=transaction)
        row = snap.to_dict() if snap.exists else None
        valid = guard["owner"] == owner and bool(row) == guard["exists"]
        if valid and row:
            valid = row.get("owner") == owner and all(row.get(k) == v for k, v in guard["fields"].items())
            valid = valid and (row.get("latest") or {}).get("view_revision") == guard["view_revision"]
            status = row["status"]
            if status in ("sharing", "paused") and row.get("lease_until", 0) <= self.clock():
                status = "disconnected"
            valid = valid and status == guard["effective_status"]
        if not valid:
            raise HTTPException(409, "Capture producer changed; refresh before editing")

    def save(self, state, expected, event, *, capture_guard=None):
        self._validate(state, event, expected)
        ref = self._document(state["lab_session_id"])
        def commit(transaction):
            current = self._owned(ref.get(transaction=transaction), state["owner_id"])
            if current["revision"] != expected:
                raise HTTPException(409, "Lab revision changed; refresh before editing")
            if capture_guard is not None:
                if state.get("workspace", {}).get("capture_session_id") != capture_guard["capture_id"]:
                    raise HTTPException(409, "Attached capture changed")
                self._verify_capture_guard(transaction, capture_guard, state["owner_id"])
            transaction.set(ref, self._body(state))
            transaction.create(self._event_ref(ref, event), {"sequence": event["event_sequence"],
                                                           "event_id": event["event_id"], "body_json": encode(event)})
        run_atomic(self.client, commit)

    def events(self, lab_id, owner, after=0, limit=None):
        ref = self._document(lab_id)
        def read(transaction):
            self._owned(ref.get(transaction=transaction), owner)
            query = ref.collection("events").where("sequence", ">", after).order_by("sequence")
            if limit is not None:
                query = query.limit(limit)
            return [json.loads(s.to_dict()["body_json"]) for s in query.stream(transaction=transaction)]
        return run_atomic(self.client, read)

    def delete(self, lab_id, owner):
        ref = self._document(lab_id)
        def commit(transaction):
            current = self._owned(ref.get(transaction=transaction), owner)
            # No state or student reports remain readable after deletion. Events are
            # physically pruned below; transactionally denying access comes first.
            transaction.set(ref, {"owner": owner, "revision": current["revision"], "deleted": True,
                                  "deleted_at_unix": self.clock()})
        run_atomic(self.client, commit)
        # Cleanup is restartable and safe after a partial failure: all API access is
        # already denied and keyed retries cannot recreate this ID.
        self.prune_deleted_events(lab_id)

    def prune_deleted_events(self, lab_id):
        ref = self._document(lab_id)
        snapshot = ref.get()
        if not snapshot.exists or not snapshot.to_dict().get("deleted"):
            raise ValueError("Only tombstoned lab journals may be pruned")
        for snapshot in ref.collection("events").stream():
            snapshot.reference.delete()


class CloudLabCreateKeys:
    """Owner/body-bound idempotency, committed with initial state and event."""
    def __init__(self, store):
        self.store = store

    def start(self, lab, owner, idem, request_hash, body):
        key_hash = hashlib.sha256(json.dumps([owner, idem], separators=(",", ":")).encode()).hexdigest()
        receipt = self.store.receipts.document(key_hash)
        with self.store.stage_create() as staged:
            projected = lab.start(owner, body)
        if len(staged) != 1:
            raise RuntimeError("Domain creation must produce one state/event pair")
        state, event = staged[0]
        if state["owner_id"] != owner:
            raise RuntimeError("Create receipt owner does not match domain state")
        ref = self.store._document(state["lab_session_id"])
        def commit(transaction):
            old = receipt.get(transaction=transaction)
            if old.exists:
                saved = old.to_dict()
                if saved.get("owner") != owner:
                    raise HTTPException(404, "Lab session not found")
                if saved["request_hash"] != request_hash:
                    raise HTTPException(409, "Idempotency key already used for a different request")
                prior = self.store._document(saved["lab_session_id"]).get(transaction=transaction)
                return lab.project(json.loads(self.store._owned(prior, owner)["state_json"])), True
            if ref.get(transaction=transaction).exists:
                raise HTTPException(409, "Lab session already exists")
            self.store._write_create(transaction, ref, state, event)
            transaction.create(receipt, {"owner": owner, "request_hash": request_hash,
                                         "lab_session_id": state["lab_session_id"], "created_at_unix": self.store.clock()})
            return projected, False
        return run_atomic(self.store.client, commit)
