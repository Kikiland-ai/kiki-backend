"""Idempotent lab creation for trusted upstreams, kept outside the frozen lab transport."""
import hashlib
import json
import re
import sqlite3

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from contracts.lab_tracking import StartLab


class _AtomicCreateStore:
    """Delegate frozen store operations; join keyed creation to its caller's transaction."""

    def __init__(self, original, keys):
        self.original = original
        self.keys = keys

    def __getattr__(self, name):
        return getattr(self.original, name)

    def create(self, state, event):
        with self.original.lock:
            if self.keys.pending is None:
                return self.original.create(state, event)
            owner, idem, request_hash = self.keys.pending
            if state['owner_id'] != owner or not self.original.db.in_transaction:
                raise RuntimeError('Keyed lab creation requires its owning transaction')
            # Do not call the original create(): its connection context commits early.
            # All three inserts share labs.sqlite's transaction, including the journal.
            self.original.db.execute('INSERT INTO lab_sessions VALUES(?,?,?,?)', (
                state['lab_session_id'], owner, state['revision'], json.dumps(state)))
            self.original.db.execute('INSERT INTO lab_events VALUES(?,?,?,?)', (
                state['lab_session_id'], event['event_id'], event['event_sequence'], json.dumps(event)))
            self.keys.remember(owner, idem, request_hash, state['lab_session_id'])


class LabCreateKeys:
    """Atomically persist a lab, its first event and its owner/body-bound replay receipt.

    The frozen domain service/store stay unchanged. The store adapter only intercepts
    keyed create; other writes retain their existing semantics. This closes the local
    SQLite crash window, not Cloud Run's separate durable/shared-state requirements.
    """

    def __init__(self, directory, store):
        self.lock = store.lock
        self.db = store.db
        self.pending = None  # Read and written only under the original store's RLock.
        self.store = _AtomicCreateStore(store, self)
        self.db.execute('''
            CREATE TABLE IF NOT EXISTS lab_create_keys (
                owner TEXT NOT NULL, idem TEXT NOT NULL, request_hash TEXT NOT NULL,
                lab_session_id TEXT NOT NULL, PRIMARY KEY(owner, idem)
            )
        ''')
        self._import_legacy(directory / 'lab-idempotency.sqlite')

    def _import_legacy(self, path):
        """Copy old receipts without modifying their database or existing labs.

        Keep receipts for deleted labs too: replay must not resurrect a deleted lab.
        Conflicting receipts fail startup rather than silently changing retry identity.
        Stop the old writer before upgrading; mixed old/new versions are unsupported.
        """
        if not path.exists():
            return
        legacy = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)
        try:
            rows = legacy.execute(
                'SELECT owner, idem, request_hash, lab_session_id FROM lab_create_keys').fetchall()
        finally:
            legacy.close()
        with self.lock, self.db:
            self.db.execute('BEGIN IMMEDIATE')
            for owner, idem, request_hash, lab_id in rows:
                old = self.find(owner, idem)
                if old and tuple(old) != (request_hash, lab_id):
                    raise RuntimeError('Conflicting legacy lab creation receipt; migration stopped')
                if old is None:
                    self.remember(owner, idem, request_hash, lab_id)

    def find(self, owner, idem):
        with self.lock:
            return self.db.execute('SELECT request_hash, lab_session_id FROM lab_create_keys WHERE owner=? AND idem=?', (owner, idem)).fetchone()

    def remember(self, owner, idem, request_hash, lab_session_id):
        # Called only inside the caller's transaction: never commit separately.
        if not self.db.in_transaction:
            raise RuntimeError('Lab creation receipt requires a transaction')
        self.db.execute('INSERT INTO lab_create_keys VALUES(?,?,?,?)', (owner, idem, request_hash, lab_session_id))

    def start(self, lab, owner, idem, request_hash, body):
        with self.lock, self.db:
            # Serialize lookup + creation across connections, not just Python threads.
            self.db.execute('BEGIN IMMEDIATE')
            old = self.find(owner, idem)
            if old:
                if old[0] != request_hash:
                    raise HTTPException(409, 'Idempotency key already used for a different request')
                return lab.project(lab.load(old[1], owner)), True
            self.pending = (owner, idem, request_hash)
            try:
                return lab.start(owner, body), False
            finally:
                self.pending = None


def start_lab_route(lab, keys, owner_of, mutation_origin):
    """POST /lab-sessions with the frozen route's limits, plus an optional Idempotency-Key.

    The same owner, key and body return the lab created first (201, Idempotency-Replayed: true);
    the same key with a different body is 409. Without the header it behaves as before.
    """

    async def start(request: Request):
        owner = owner_of(request)
        mutation_origin(request)
        idem = request.headers.get('idempotency-key')
        if idem is not None and not re.fullmatch(r'[A-Za-z0-9_.:-]{1,100}', idem):
            raise HTTPException(422, 'Idempotency-Key must be 1–100 ASCII identifier characters')
        data = bytearray()
        async for chunk in request.stream():
            data.extend(chunk)
            if len(data) > 12000:
                raise HTTPException(413, 'Lab request is too large')
        try:
            body = StartLab.model_validate_json(data)
        except ValueError:
            # Avoid echoing arbitrary student reports into validation/logging output.
            raise HTTPException(422, 'Invalid lab request fields') from None
        if idem is None:
            return JSONResponse(lab.start(owner, body), status_code=201)
        request_hash = hashlib.sha256(json.dumps(body.model_dump(mode='json'), sort_keys=True).encode()).hexdigest()
        state, replayed = keys.start(lab, owner, idem, request_hash, body)
        return JSONResponse(state, status_code=201,
                            headers={'Idempotency-Replayed': 'true'} if replayed else {})

    return start
