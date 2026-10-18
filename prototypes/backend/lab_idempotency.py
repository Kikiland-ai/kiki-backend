"""Idempotent lab creation for trusted upstreams, kept outside the frozen lab transport."""
import hashlib
import json
import re
import sqlite3
import threading

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from contracts.lab_tracking import StartLab


class LabCreateKeys:
    """Maps (owner, Idempotency-Key) to the lab it created and the request it was used for."""

    def __init__(self, directory):
        self.lock = threading.Lock()
        self.db = sqlite3.connect(directory / 'lab-idempotency.sqlite', check_same_thread=False)
        self.db.executescript('''
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS lab_create_keys (
                owner TEXT NOT NULL, idem TEXT NOT NULL, request_hash TEXT NOT NULL,
                lab_session_id TEXT NOT NULL, PRIMARY KEY(owner, idem)
            );
        ''')

    def find(self, owner, idem):
        return self.db.execute('SELECT request_hash, lab_session_id FROM lab_create_keys WHERE owner=? AND idem=?', (owner, idem)).fetchone()

    def remember(self, owner, idem, request_hash, lab_session_id):
        with self.db:
            self.db.execute('INSERT INTO lab_create_keys VALUES(?,?,?,?)', (owner, idem, request_hash, lab_session_id))


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
        # No await below: the lookup, creation and record run as one step for this single-instance service.
        with keys.lock:
            old = keys.find(owner, idem)
            if old:
                if old[0] != request_hash:
                    raise HTTPException(409, 'Idempotency key already used for a different request')
                return JSONResponse(lab.project(lab.load(old[1], owner)), status_code=201, headers={'Idempotency-Replayed': 'true'})
            state = lab.start(owner, body)
            keys.remember(owner, idem, request_hash, state['lab_session_id'])
        return JSONResponse(state, status_code=201)

    return start
