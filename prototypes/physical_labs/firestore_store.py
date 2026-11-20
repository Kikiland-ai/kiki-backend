"""Durable preparation sessions behind the existing private cloud lab API."""

import json

from fastapi import HTTPException

from prototypes.cloud_lab.store import run_atomic
from .service import PreparationService, digest


def encode(value):
    # Packs contain arrays of coordinate vectors and connection pairs.
    # Firestore does not support nested arrays in a document field.
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def read_session(snapshot):
    if not snapshot.exists:
        raise HTTPException(404, "Preparation session not found")
    row = snapshot.to_dict()
    return json.loads(row["state"]), json.loads(row["pack"])


class FirestorePreparationService(PreparationService):
    def __init__(self, client, collection_prefix, packs=None):
        self.client = client
        self.owners = client.collection(f"{collection_prefix}_physical_owners")
        self.packs = self.validated_packs(packs)

    def sessions(self, owner):
        return self.owners.document(digest(owner)).collection("sessions")

    def create(self, owner, key, body):
        pack, body_hash = self.creation_input(body)
        sessions = self.sessions(owner)
        key_ref = self.owners.document(digest(owner)).collection("creation_keys").document(digest(key))
        state = self.new_session(pack, body)

        def persist(transaction):
            previous = key_ref.get(transaction=transaction).to_dict()
            if previous is not None:
                if previous["body_hash"] != body_hash:
                    raise HTTPException(409, "Creation key already used for another request")
                saved, pinned = read_session(sessions.document(previous["session_id"]).get(transaction=transaction))
                return self.project(saved, pinned)
            transaction.create(sessions.document(state["session_id"]), {
                "state": encode(state), "pack": encode(pack), "created_at": state["created_at"],
            })
            transaction.create(key_ref, {"session_id": state["session_id"], "body_hash": body_hash})
            return self.project(state, pack)

        return run_atomic(self.client, persist)

    def saved(self, session_id, owner):
        return read_session(self.sessions(owner).document(session_id).get())

    def list_sessions(self, owner):
        snapshots = self.sessions(owner).order_by("created_at", direction="DESCENDING").limit(100).stream()
        fields = ("session_id", "revision", "stage", "experiment_id", "title", "updated_at", "mode")
        rows = (self.project(*read_session(snapshot)) for snapshot in snapshots)
        return [{field: row[field] for field in fields} for row in rows]

    def event(self, session_id, owner, event):
        session = self.sessions(owner).document(session_id)
        receipt = session.collection("events").document(event.event_id)
        body_hash = digest(event.model_dump())

        def persist(transaction):
            state, pack = read_session(session.get(transaction=transaction))
            previous = receipt.get(transaction=transaction).to_dict()
            if previous is not None:
                if previous["body_hash"] != body_hash:
                    raise HTTPException(409, "Event ID already used for another request")
                return json.loads(previous["response"])
            response = self.advance(state, pack, event)
            transaction.update(session, {"state": encode(state)})
            transaction.create(receipt, {"body_hash": body_hash, "response": encode(response)})
            return response

        return run_atomic(self.client, persist)
