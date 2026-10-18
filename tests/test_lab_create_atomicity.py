"""Offline crash/retry and migration proofs for the composed lab-create boundary."""

import hashlib
import json
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from contracts.lab_tracking import StartLab
from prototypes.backend.app import create_app
from prototypes.backend.lab_idempotency import LabCreateKeys
from prototypes.lab_tracking.service import LabService

BODY = StartLab(model_name='atomicity_fixture', operator_trial=True,
                progression_mode='screen_guided')
REQUEST_HASH = hashlib.sha256(
    json.dumps(BODY.model_dump(mode='json'), sort_keys=True).encode()).hexdigest()
ROOT = Path(__file__).resolve().parents[1]


class LabCreateAtomicityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.connections = []

    def tearDown(self):
        for db in self.connections:
            db.close()
        self.temp.cleanup()

    def service(self):
        lab = LabService(self.directory, None, analyzer=SimpleNamespace(configured=False))
        self.connections.append(lab.store.db)
        keys = LabCreateKeys(self.directory, lab.store)
        lab.store = keys.store
        return lab, keys

    def start(self, lab, keys, owner='fb:atomicity', idem='create-1'):
        return keys.start(lab, owner, idem, REQUEST_HASH, BODY)

    def counts(self, db):
        return tuple(db.execute('SELECT COUNT(*) FROM ' + table).fetchone()[0]
                     for table in ('lab_sessions', 'lab_events', 'lab_create_keys'))

    def test_receipt_failure_rolls_back_lab_and_first_event_then_retry_succeeds(self):
        lab, keys = self.service()
        original = keys.remember

        def fail_after_insert(*args):
            original(*args)
            raise RuntimeError('injected receipt failure')

        with (patch.object(keys, 'remember', side_effect=fail_after_insert),
              self.assertRaisesRegex(RuntimeError, 'injected receipt failure')):
            self.start(lab, keys)
        self.assertEqual(self.counts(keys.db), (0, 0, 0))
        self.assertIsNone(keys.pending)
        self.assertFalse(keys.db.in_transaction)
        state, replayed = self.start(lab, keys)
        self.assertFalse(replayed)
        again, replayed = self.start(lab, keys)
        self.assertTrue(replayed)
        self.assertEqual(state['lab_session_id'], again['lab_session_id'])
        self.assertEqual(self.counts(keys.db), (1, 1, 1))

    def test_projection_failure_rolls_back_all_three_writes(self):
        lab, keys = self.service()
        with (patch.object(lab, 'project', side_effect=RuntimeError('injected projection failure')),
              self.assertRaisesRegex(RuntimeError, 'injected projection failure')):
            self.start(lab, keys)
        self.assertEqual(self.counts(keys.db), (0, 0, 0))
        self.assertFalse(self.start(lab, keys)[1])

    def test_two_connections_racing_create_one_lab_and_receipt(self):
        pairs = [self.service(), self.service()]
        gate = threading.Barrier(2)

        def create(pair):
            gate.wait(timeout=5)
            return self.start(*pair)

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(create, pairs))
        self.assertEqual(len({state['lab_session_id'] for state, _ in results}), 1)
        self.assertEqual(sorted(replay for _, replay in results), [False, True])
        self.assertEqual(self.counts(pairs[0][1].db), (1, 1, 1))

    def test_owner_isolation_body_conflict_and_deleted_lab_tombstone(self):
        lab, keys = self.service()
        first, _ = self.start(lab, keys)
        other, _ = self.start(lab, keys, owner='fb:other')
        self.assertNotEqual(first['lab_session_id'], other['lab_session_id'])
        with self.assertRaises(HTTPException) as error:
            keys.start(lab, 'fb:atomicity', 'create-1', 'different-hash', BODY)
        self.assertEqual(error.exception.status_code, 409)
        lab.store.delete(first['lab_session_id'], 'fb:atomicity')
        with self.assertRaises(HTTPException) as error:
            self.start(lab, keys)
        self.assertEqual(error.exception.status_code, 404)
        self.assertEqual(self.counts(keys.db), (1, 1, 2))

    def legacy_receipt(self, lab_id):
        path = self.directory / 'lab-idempotency.sqlite'
        with closing(sqlite3.connect(path)) as db, db:
            db.execute('CREATE TABLE lab_create_keys (owner TEXT, idem TEXT, '
                       'request_hash TEXT, lab_session_id TEXT, PRIMARY KEY(owner,idem))')
            db.execute('INSERT INTO lab_create_keys VALUES(?,?,?,?)',
                       ('fb:atomicity', 'create-1', REQUEST_HASH, lab_id))
        return path

    def test_legacy_receipts_import_replay_and_repeat_without_rewriting_source(self):
        lab, keys = self.service()
        state = lab.start('fb:atomicity', BODY)  # Simulate pre-upgrade creation.
        path = self.legacy_receipt(state['lab_session_id'])
        before = path.read_bytes()
        restarted, migrated = self.service()
        replay, replayed = self.start(restarted, migrated)
        self.assertTrue(replayed)
        self.assertEqual(replay['lab_session_id'], state['lab_session_id'])
        self.service()  # Import is idempotent on another restart.
        self.assertEqual(keys.db.execute('SELECT COUNT(*) FROM lab_create_keys').fetchone()[0], 1)
        self.assertEqual(path.read_bytes(), before)

    def test_conflicting_legacy_receipt_fails_closed_without_overwriting_data(self):
        lab, keys = self.service()
        state, _ = self.start(lab, keys)
        path = self.legacy_receipt('different-lab')
        before = path.read_bytes()
        with self.assertRaisesRegex(RuntimeError, 'Conflicting legacy'):
            LabCreateKeys(self.directory, keys.store.original)
        self.assertEqual(keys.find('fb:atomicity', 'create-1')[1], state['lab_session_id'])
        self.assertEqual(self.counts(keys.db), (1, 1, 1))
        self.assertEqual(path.read_bytes(), before)

    def test_legacy_deleted_lab_receipt_is_preserved_without_resurrection(self):
        self.legacy_receipt('deleted-lab')
        lab, keys = self.service()
        with self.assertRaises(HTTPException) as error:
            self.start(lab, keys)
        self.assertEqual(error.exception.status_code, 404)
        self.assertEqual(self.counts(keys.db), (0, 0, 1))

    def test_abrupt_process_exit_before_commit_rolls_back_on_restart(self):
        for phase in ('before_receipt', 'after_receipt'):
            with self.subTest(phase=phase):
                directory = self.directory / phase
                directory.mkdir()
                self.run_crash(directory, phase)
                # A fresh process has no Python locks or rollback handlers to help it.
                with closing(sqlite3.connect(directory / 'labs.sqlite')) as db:
                    self.assertEqual(self.counts(db), (0, 0, 0))
                original_directory = self.directory
                self.directory = directory
                try:
                    lab, keys = self.service()
                    self.assertFalse(self.start(lab, keys)[1])
                    self.assertEqual(self.counts(keys.db), (1, 1, 1))
                finally:
                    self.directory = original_directory

    def test_abrupt_exit_after_commit_replays_same_lab_after_restart(self):
        self.run_crash(self.directory, 'after_commit')
        with closing(sqlite3.connect(self.directory / 'labs.sqlite')) as db:
            self.assertEqual(self.counts(db), (1, 1, 1))
            lab_id = db.execute('SELECT id FROM lab_sessions').fetchone()[0]
        lab, keys = self.service()
        replay, replayed = self.start(lab, keys)
        self.assertTrue(replayed)
        self.assertEqual(replay['lab_session_id'], lab_id)
        self.assertEqual(keys.db.execute('SELECT COUNT(*) FROM lab_sessions').fetchone()[0], 1)

    def run_crash(self, directory, phase):
        script = '''
import os, sys, hashlib, json
from pathlib import Path
from types import SimpleNamespace
from contracts.lab_tracking import StartLab
from prototypes.backend.lab_idempotency import LabCreateKeys
from prototypes.lab_tracking.service import LabService
body = StartLab(model_name='atomicity_fixture', operator_trial=True, progression_mode='screen_guided')
digest = hashlib.sha256(json.dumps(body.model_dump(mode='json'), sort_keys=True).encode()).hexdigest()
lab = LabService(Path(sys.argv[1]), None, analyzer=SimpleNamespace(configured=False))
keys = LabCreateKeys(Path(sys.argv[1]), lab.store)
lab.store = keys.store
remember = keys.remember
def crash(*args):
    if sys.argv[2] == 'after_receipt':
        remember(*args)
    os._exit(73)
if sys.argv[2] != 'after_commit':
    keys.remember = crash
keys.start(lab, 'fb:atomicity', 'create-1', digest, body)
os._exit(73)
'''
        result = subprocess.run([sys.executable, '-X', 'utf8', '-B', '-c', script,
                                 str(directory), phase], check=False, cwd=ROOT, capture_output=True,
                                text=True, encoding='utf-8', timeout=20)
        self.assertEqual(result.returncode, 73, result.stderr)

    def test_http_failure_then_restart_retry_returns_one_lab_with_proxy_boundary(self):
        secret = 'offline-fixture-proxy-secret-32-characters'
        headers = {'x-kiki-proxy-key': secret, 'x-kiki-owner': 'fb:atomicity',
                   'origin': 'http://testserver', 'Idempotency-Key': 'create-1'}
        app = create_app(self.directory, analyzer=SimpleNamespace(configured=False),
                         proxy_secret=secret)
        self.connections.extend([app.state.store.db, app.state.lab.store.db])
        with TestClient(app, raise_server_exceptions=False) as client:
            with patch.object(app.state.lab_keys, 'remember', side_effect=RuntimeError('injected')):
                failed = client.post('/lab-sessions', json=BODY.model_dump(), headers=headers)
                self.assertEqual(failed.status_code, 500)
            self.assertEqual(self.counts(app.state.lab_keys.db), (0, 0, 0))
        restarted = create_app(self.directory, analyzer=SimpleNamespace(configured=False),
                               proxy_secret=secret)
        self.connections.extend([restarted.state.store.db, restarted.state.lab.store.db])
        with TestClient(restarted) as client:
            first = client.post('/lab-sessions', json=BODY.model_dump(), headers=headers)
            replay = client.post('/lab-sessions', json=BODY.model_dump(), headers=headers)
            self.assertEqual((first.status_code, replay.status_code), (201, 201))
            self.assertEqual(first.json()['lab_session_id'], replay.json()['lab_session_id'])
            self.assertEqual(replay.headers['idempotency-replayed'], 'true')
            self.assertEqual(self.counts(restarted.state.lab_keys.db), (1, 1, 1))
            self.assertEqual(client.post('/lab-sessions', json=BODY.model_dump(),
                                         headers={'origin': 'http://testserver'}).status_code, 401)


if __name__ == '__main__':
    unittest.main()
