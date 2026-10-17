import importlib.util
import json
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest

from prototypes.concept_library.library import DATABASE, ROOT, ConceptLibrary, build


class LibraryTests(unittest.TestCase):
    def test_all_ten_packets_and_full_concept_audio_are_queryable(self):
        lib = ConceptLibrary()
        try:
            self.assertEqual(len(lib.concepts()), 10)
            packet = lib.packet('C-AM-04')
            self.assertEqual(packet['narration'][0]['scope'], 'concept')
            self.assertEqual(len(packet['narration'][0]['placardIds']), 4)
            data, mime = lib.asset(packet['narration'][0]['audioSha256'])
            self.assertEqual(mime, 'audio/wav')
            self.assertEqual(len(data), packet['narration'][0]['bytes'])
            with self.assertRaises(KeyError):
                lib.packet("C-AM-08' OR 1=1 --")
        finally:
            lib.close()

    def test_database_rebuild_is_identical_and_failed_build_keeps_previous_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / 'library.sqlite3'
            build(db)
            self.assertEqual(db.read_bytes(), DATABASE.read_bytes())
            before = db.read_bytes()
            with self.assertRaisesRegex(ValueError, 'No concept packets'):
                build(db, Path(directory))
            self.assertEqual(db.read_bytes(), before)

    def test_database_and_file_tampering_are_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            db = root / 'library.sqlite3'
            shutil.copyfile(DATABASE, db)
            with sqlite3.connect(db) as connection:
                row = connection.execute('SELECT asset_id,relative_path FROM assets WHERE mime_type=? LIMIT 1', ('audio/wav',)).fetchone()
                connection.execute("UPDATE packets SET packet_json='{}' WHERE concept_id='C-AM-08'")
            dest = root / row[1]
            dest.parent.mkdir(parents=True)
            dest.write_bytes((ROOT / row[1]).read_bytes()[:-2] + b'\x00\x00')
            lib = ConceptLibrary(db, root)
            try:
                with self.assertRaisesRegex(ValueError, 'packet checksum'):
                    lib.packet('C-AM-08')
                with self.assertRaisesRegex(ValueError, 'Asset checksum'):
                    lib.asset(row[0])
            finally:
                lib.close()


WEB = os.environ.get('KIKI_WEB_CHECKOUT')


@unittest.skipUnless(WEB and importlib.util.find_spec('firebase_admin'), 'Set KIKI_WEB_CHECKOUT and install the merged API dependencies for bridge checks')
class MergedWebTests(unittest.TestCase):
    def test_phase_package_binds_to_real_merged_contract(self):
        from prototypes.concept_library.web_adapter import package
        p, exclusions = package('C-AM-08', WEB)
        self.assertEqual(exclusions, [])
        self.assertEqual(len(p.manifest.narration), 4)
        self.assertEqual(p.manifest.artifacts[0].renderer, 'coherent-phase-recovery/v1')
        self.assertEqual(set(p.assets), set(p.record['assets']))
        self.assertEqual(p.manifest.narration[0].speech.generatedAt, 'not_recorded_in_recovered_packet')
        again, _ = package('C-AM-08', WEB)
        self.assertEqual(p.record, again.record)

    def test_unsupported_audio_and_scene_stay_in_original_library(self):
        from prototypes.concept_library.web_adapter import package
        p, exclusions = package('C-AM-04', WEB)
        self.assertEqual(p.manifest.narration, [])
        self.assertEqual(p.manifest.artifacts, [])
        self.assertEqual(len(exclusions), 2)
        lib = ConceptLibrary()
        try:
            self.assertEqual(len(lib.packet('C-AM-04')['narration']), 1)
        finally:
            lib.close()


if __name__ == '__main__':
    unittest.main()
