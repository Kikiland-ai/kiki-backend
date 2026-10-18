"""Batch acceptance for all ten saved CAM modules, with no generation or cloud writes."""

import copy
import importlib.util
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from pydantic import ValidationError

from contracts.concept_canvas import ConceptCanvasArtifact

ROOT = Path(__file__).resolve().parents[1]
WEB = os.environ.get("KIKI_WEB_CHECKOUT")


@unittest.skipUnless(
    WEB and importlib.util.find_spec("firebase_admin"),
    "Set KIKI_WEB_CHECKOUT and use API dependencies",
)
class AllCamTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from prototypes.concept_library.web_adapter import package

        cls.prepared = {
            f"C-AM-{i:02}": package(f"C-AM-{i:02}", WEB, contract="candidate-cam")
            for i in range(1, 11)
        }

    def test_all_ten_export_without_exclusions_and_correct_clip_scopes(self):
        self.assertEqual(
            sum(len(p.manifest.narration) for p, _ in self.prepared.values()), 26
        )
        self.assertEqual(
            sum(len(p.manifest.artifacts) for p, _ in self.prepared.values()), 10
        )
        for cid, (p, exclusions) in self.prepared.items():
            self.assertEqual(exclusions, [])
            self.assertEqual(p.record["schema"], "concept-media-revision/v1")
            self.assertEqual(p.manifest.schema_, "concept-media-manifest/v1")
            self.assertEqual(p.manifest.catalogVersion, "am-51187527300cba2fa3cca868")
            if cid in (
                "C-AM-04",
                "C-AM-05",
                "C-AM-06",
                "C-AM-07",
                "C-AM-09",
                "C-AM-10",
            ):
                [clip] = p.manifest.narration
                self.assertEqual(clip.scope, "concept")
                self.assertEqual(len(clip.placardIds), 4)
                self.assertFalse(hasattr(clip, "placardId"))
                self.assertEqual(clip.timing.alignment, "not_performed")

    def test_canvas_kinds_and_checked_in_schema_cover_the_entire_library(self):
        from kiki_api import media_models

        from contracts.concept_canvas import POLICIES
        from prototypes.concept_library.candidate_contract import (
            candidate_manifest_model,
        )

        self.assertEqual(len(POLICIES["concepts"]), 10)
        for cid, (p, _) in self.prepared.items():
            if cid == "C-AM-08":
                continue
            [artifact] = p.manifest.artifacts
            self.assertEqual(artifact.renderer, "cam-concept-canvas/v1")
            self.assertEqual(artifact.scene.kind, POLICIES["concepts"][cid]["kind"])
        self.assertEqual(
            candidate_manifest_model(media_models).model_json_schema(by_alias=True),
            json.loads(
                (ROOT / "contracts/concept-media-cam-candidate.schema.json").read_text(
                    encoding="utf-8"
                )
            ),
        )

    def test_existing_web_bilingual_c_am_08_is_preserved_exactly(self):
        package, _ = self.prepared["C-AM-08"]
        preview = json.loads(
            (Path(WEB) / "apps/web/src/fixtures/concept-media-C-AM-08.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(package.record["manifest"], preview["manifest"])
        self.assertEqual(sum(c.lang == "en" for c in package.manifest.narration), 4)
        self.assertEqual(package.manifest.mediaRevision, "cm-e0f086007cc9f2062af093f3")

    def test_canvas_rejects_wrong_kind_controls_model_hash_and_nonfinite_samples(self):
        original = self.prepared["C-AM-04"][0].record["manifest"]["artifacts"][0]
        cases = []
        value = copy.deepcopy(original)
        value["scene"]["kind"] = "pm"
        cases.append(value)
        value = copy.deepcopy(original)
        value["scene"]["controls"][0]["max"] = 10000
        cases.append(value)
        value = copy.deepcopy(original)
        value["modelBindings"] = [
            {**b, "sha256": "0" * 64} for b in value["modelBindings"]
        ]
        cases.append(value)
        value = copy.deepcopy(original)
        value["behaviorTests"][0]["samples"][0]["values"][0] = float("nan")
        cases.append(value)
        for case in cases:
            with self.assertRaises(ValidationError):
                ConceptCanvasArtifact.model_validate(case)

    def test_concept_audio_rejects_reordered_coverage_and_wrong_text_hash(self):
        from prototypes.concept_library.library import ConceptLibrary
        from prototypes.concept_library.web_adapter import package

        lib = ConceptLibrary()
        try:
            original = lib.packet("C-AM-04")
            for mutate in ("order", "hash", "speech"):
                packet = copy.deepcopy(original)
                if mutate == "order":
                    packet["narration"][0]["placardIds"].reverse()
                elif mutate == "hash":
                    packet["narration"][0]["displayTextSha256"] = "0" * 64
                else:
                    packet["narration"][0]["speechTextSha256"] = "0" * 64
                with (
                    patch.object(lib, "packet", return_value=packet),
                    self.assertRaises(ValueError),
                ):
                    package("C-AM-04", WEB, lib, contract="candidate-cam")
        finally:
            lib.close()

    def test_legacy_v1_remains_unchanged_for_all_ten(self):
        from prototypes.concept_library.web_adapter import package

        expected = json.loads(
            (ROOT / "tests/fixtures/cam-legacy-revisions.json").read_text()
        )
        for cid, revision in expected.items():
            p, _ = package(cid, WEB)
            self.assertEqual(p.manifest.mediaRevision, revision)

    def test_batch_candidate_publication_is_blocked_before_any_cloud_access(self):
        result = subprocess.run(
            [
                sys.executable,
                "-X",
                "utf8",
                "-B",
                str(ROOT / "scripts/publish-concept-library.py"),
                "--web-root",
                "missing",
                "--contract",
                "candidate-cam",
                "--apply",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("export-only", result.stderr)


if __name__ == "__main__":
    unittest.main()
