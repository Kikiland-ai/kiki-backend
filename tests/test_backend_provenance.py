"""Upgrade backups and source provenance must prevent misleading adoption receipts."""
import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from prototypes.backend.provenance import (
    backup_lab_databases,
    source_receipt,
    verify_source,
)


class BackendProvenanceTests(unittest.TestCase):
    def test_wal_data_and_legacy_receipts_survive_backup_without_changing_originals(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('labs.sqlite', 'lab-idempotency.sqlite'):
                with closing(sqlite3.connect(root / name)) as db:
                    db.execute('PRAGMA journal_mode=WAL')
                    db.execute('CREATE TABLE fixture (id TEXT PRIMARY KEY)')
                    db.execute('INSERT INTO fixture VALUES (?)', ('synthetic',))
                    db.commit()
                    manifest = backup_lab_databases(root, root / ('backup-' + name))
                    target = Path(manifest['directory']) / name
                    with closing(sqlite3.connect(target)) as saved:
                        self.assertEqual(saved.execute('SELECT id FROM fixture').fetchone()[0], 'synthetic')
                    self.assertEqual(db.execute('SELECT id FROM fixture').fetchone()[0], 'synthetic')
            with self.assertRaises(FileExistsError):
                backup_lab_databases(root, root / 'backup-labs.sqlite')

    def test_candidate_hash_change_or_missing_ancestry_cannot_claim_verified_source(self):
        actual = source_receipt(Path(__file__).resolve().parents[1])
        self.assertTrue(actual['pr7_ancestor'])
        self.assertIn('prototypes/backend/lab_idempotency.py', actual['runtime_files'])
        self.assertIn('prototypes/floating_guidance/extension/background.js', actual['runtime_files'])
        self.assertFalse(any('.env' in name or '/work/' in name for name in actual['runtime_files']))
        verify_source(actual, json.loads(json.dumps(actual)))
        with self.assertRaisesRegex(ValueError, 'differs'):
            verify_source({**actual, 'runtime_source_sha256': 'changed'}, actual)
        with self.assertRaisesRegex(ValueError, 'PR #7'):
            verify_source({**actual, 'pr7_ancestor': False}, actual)


if __name__ == '__main__':
    unittest.main()
