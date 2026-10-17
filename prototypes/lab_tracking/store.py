"""Single-instance SQLite projection + atomic append-only event journal."""

import json
import sqlite3
import threading

from fastapi import HTTPException


class LabStore:
    def __init__(self, directory):
        self.lock = threading.RLock()
        self.db = sqlite3.connect(directory / "labs.sqlite", check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS lab_sessions (
                id TEXT PRIMARY KEY, owner TEXT NOT NULL, revision INTEGER NOT NULL,
                state_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS lab_events (
                session_id TEXT NOT NULL, event_id TEXT NOT NULL, sequence INTEGER NOT NULL,
                body TEXT NOT NULL, PRIMARY KEY(session_id, event_id), UNIQUE(session_id,sequence)
            );
        """)

    def load(self, lab_id, owner):
        with self.lock:
            row = self.db.execute("SELECT state_json FROM lab_sessions WHERE id=? AND owner=?", (lab_id, owner)).fetchone()
        if not row:
            raise HTTPException(404, "Lab session not found")
        return json.loads(row[0])

    def list(self, owner):
        with self.lock:
            rows = self.db.execute("SELECT state_json FROM lab_sessions WHERE owner=? ORDER BY rowid DESC LIMIT 8", (owner,)).fetchall()
        return [json.loads(row[0]) for row in rows]

    def all(self):
        with self.lock:
            return [json.loads(r[0]) for r in self.db.execute("SELECT state_json FROM lab_sessions").fetchall()]

    def create(self, state, event):
        with self.lock, self.db:
            self.db.execute("INSERT INTO lab_sessions VALUES(?,?,?,?)", (state["lab_session_id"], state["owner_id"], state["revision"], json.dumps(state)))
            self.db.execute("INSERT INTO lab_events VALUES(?,?,?,?)", (state["lab_session_id"], event["event_id"], event["event_sequence"], json.dumps(event)))

    def save(self, state, expected, event):
        with self.lock, self.db:
            changed = self.db.execute("UPDATE lab_sessions SET revision=?,state_json=? WHERE id=? AND owner=? AND revision=?",
                                      (state["revision"], json.dumps(state), state["lab_session_id"], state["owner_id"], expected)).rowcount
            if not changed:
                raise HTTPException(409, "Lab revision changed; refresh before editing")
            self.db.execute("INSERT INTO lab_events VALUES(?,?,?,?)", (state["lab_session_id"], event["event_id"], event["event_sequence"], json.dumps(event)))

    def events(self, lab_id, owner, after=0, limit=None):
        self.load(lab_id, owner)
        with self.lock:
            sql = "SELECT body FROM lab_events WHERE session_id=? AND sequence>? ORDER BY sequence"
            args = (lab_id, after)
            if limit is not None:
                sql += " LIMIT ?"
                args += (limit,)
            return [json.loads(r[0]) for r in self.db.execute(sql, args).fetchall()]

    def delete(self, lab_id, owner):
        self.load(lab_id, owner)
        with self.lock, self.db:
            self.db.execute("DELETE FROM lab_events WHERE session_id=?", (lab_id,))
            self.db.execute("DELETE FROM lab_sessions WHERE id=? AND owner=?", (lab_id, owner))
