"""Contract rejection, numerical examples and compatibility with the actual web schema."""

import copy
import importlib.util
import json
import math
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from pydantic import ValidationError

from contracts.signal_scene import SignalParametersScene, evaluate_signal

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/signal-parameters-v1.json"
WEB = os.environ.get("KIKI_WEB_CHECKOUT")


class SignalContractTests(unittest.TestCase):
    def setUp(self):
        self.scene = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_saved_fixture_and_independent_physical_examples(self):
        SignalParametersScene.model_validate(self.scene)
        self.assertEqual(
            SignalParametersScene.model_json_schema(),
            json.loads(
                (ROOT / "contracts/signal-parameters-v1.schema.json").read_text(
                    encoding="utf-8"
                )
            ),
        )
        controls = {"amplitude": 2, "frequency": 100, "phase": 90}
        self.assertAlmostEqual(evaluate_signal(controls, "periodSeconds"), 0.01)
        self.assertAlmostEqual(
            evaluate_signal(controls, "angularFrequency"), 200 * math.pi
        )
        self.assertAlmostEqual(
            evaluate_signal({**controls, "timeSeconds": 0}, "signal"), 2
        )
        self.assertAlmostEqual(
            evaluate_signal({**controls, "timeSeconds": 0}, "reference"), 0
        )
        self.assertAlmostEqual(
            evaluate_signal({**controls, "timeSeconds": 0.0025}, "signal"), 0
        )

    def test_bad_units_missing_controls_and_untrusted_fields_are_rejected(self):
        cases = []
        unit = copy.deepcopy(self.scene)
        unit["controls"][2]["unit"] = "radian"
        cases.append(unit)
        missing = copy.deepcopy(self.scene)
        missing["controls"].pop()
        cases.append(missing)
        duplicate = copy.deepcopy(self.scene)
        duplicate["controls"][2] = duplicate["controls"][0]
        cases.append(duplicate)
        injected = copy.deepcopy(self.scene)
        injected["formula"] = '__import__("os")'
        cases.append(injected)
        wrong_reference = copy.deepcopy(self.scene)
        wrong_reference["reference"] = "follow_signal_amplitude"
        cases.append(wrong_reference)
        readout = copy.deepcopy(self.scene)
        readout["outputs"][0]["unit"] = "ms"
        cases.append(readout)
        aliasing = copy.deepcopy(self.scene)
        aliasing["sampleIntervals"] = 20
        cases.append(aliasing)
        for case in cases:
            with (
                self.subTest(case=cases.index(case)),
                self.assertRaises(ValidationError),
            ):
                SignalParametersScene.model_validate(case)

    def test_invalid_scientific_examples_and_nonfinite_values_are_rejected(self):
        wrong = copy.deepcopy(self.scene)
        wrong["behaviorTests"][0]["expected"] = 10
        nan = copy.deepcopy(self.scene)
        nan["behaviorTests"][0]["expected"] = float("nan")
        missing_trace = copy.deepcopy(self.scene)
        missing_trace["behaviorTests"] = [
            t for t in missing_trace["behaviorTests"] if t["output"] != "reference"
        ]
        for case in (wrong, nan, missing_trace):
            with self.assertRaises(ValidationError):
                SignalParametersScene.model_validate(case)
        base = {"amplitude": 1, "frequency": 100, "phase": 0}
        for values in (
            {**base, "frequency": 0},
            {**base, "phase": 7},
            {**base, "frequency": float("inf")},
            {**base, "amplitude": True},
            {**base, "unexpected": 1},
        ):
            with self.assertRaises(ValueError):
                evaluate_signal(values, "periodSeconds")
        for time in (-0.001, 0.021, float("nan")):
            with self.assertRaises(ValueError):
                evaluate_signal({**base, "timeSeconds": time}, "signal")


@unittest.skipUnless(
    WEB and importlib.util.find_spec("firebase_admin"),
    "Set KIKI_WEB_CHECKOUT and use web API dependencies",
)
class CandidateBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from prototypes.concept_library.web_adapter import connect

        connect(WEB)

    def test_signal_export_is_deterministic_and_preserves_audio(self):
        from prototypes.concept_library.web_adapter import package

        first, exclusions = package("C-AM-01", WEB, contract="candidate-signal")
        again, _ = package("C-AM-01", WEB, contract="candidate-signal")
        legacy, legacy_exclusions = package("C-AM-01", WEB)
        self.assertEqual(exclusions, [])
        self.assertEqual(first.record, again.record)
        self.assertEqual(
            first.record,
            json.loads(
                (
                    ROOT / "tests/fixtures/concept-media-C-AM-01-candidate.json"
                ).read_text(encoding="utf-8")
            ),
        )
        self.assertEqual(first.assets, legacy.assets)
        self.assertEqual(
            [r.model_dump() for r in first.manifest.narration],
            [r.model_dump() for r in legacy.manifest.narration],
        )
        self.assertEqual(legacy.manifest.artifacts, [])
        self.assertEqual(len(legacy_exclusions), 1)
        scene = first.manifest.artifacts[0].model_dump()
        self.assertEqual(scene, json.loads(FIXTURE.read_text(encoding="utf-8")))
        self.assertEqual(len(first.manifest.narration), 4)
        self.assertEqual(first.manifest.schema_, "concept-media-manifest/v1")

    def test_c_am_08_legacy_revision_and_phase_payload_are_unchanged(self):
        from prototypes.concept_library.web_adapter import package

        old, exclusions = package("C-AM-08", WEB)
        candidate, _ = package("C-AM-08", WEB, contract="candidate-signal")
        self.assertEqual(exclusions, [])
        self.assertEqual(old.manifest.mediaRevision, "cm-09967975820d6468c9272a38")
        self.assertEqual(old.manifest.schema_, "concept-media-manifest/v1")
        self.assertEqual(
            old.manifest.artifacts[0].model_dump(),
            candidate.manifest.artifacts[0].model_dump(),
        )
        self.assertEqual(old.assets, candidate.assets)

    def test_current_python_scene_union_needs_extension_and_whole_audio_stays_explicit(
        self,
    ):
        from kiki_api.media_models import MediaManifest

        from prototypes.concept_library.web_adapter import package

        candidate, _ = package("C-AM-01", WEB, contract="candidate-signal")
        with self.assertRaises(ValidationError):
            MediaManifest.model_validate(candidate.record["manifest"])
        unsupported, exclusions = package("C-AM-04", WEB, contract="candidate-signal")
        self.assertEqual(unsupported.manifest.narration, [])
        self.assertEqual(unsupported.manifest.artifacts, [])
        self.assertEqual({e["kind"] for e in exclusions}, {"narration", "scene"})

    def test_source_drift_and_saved_scene_drift_are_rejected(self):
        from prototypes.concept_library.library import ConceptLibrary
        from prototypes.concept_library.signal_scene import project_signal
        from prototypes.concept_library.web_adapter import connect

        _, media, catalogs = connect(WEB)
        from kiki_api.learning_models import Lesson

        web = Path(WEB)
        catalog = catalogs.build_catalog(
            web / "data-model/ledgers/electronics/analog-modulation.json",
            web / "data-model/cases/analog-modulation-odia.json",
        )
        base = f"learningCatalog/LP-ANALOG-MODULATION/versions/{catalog.version}"
        source = catalog.documents[base + "/sourceConcepts/C-AM-01"]
        lesson = Lesson.model_validate(catalog.documents[base + "/lessons/C-AM-01"])
        lib = ConceptLibrary()
        try:
            packet = lib.packet("C-AM-01")
            changed = copy.deepcopy(source)
            changed["explanation"]["modalities"]["interactive"]["outputs"][0][
                "formula"
            ] = "eval(user_input)"
            with self.assertRaises(ValueError):
                project_signal(packet, changed, lesson, media, lib)
            changed_packet = copy.deepcopy(packet)
            changed_packet["scene"]["controls"][0]["max"] = 20
            with self.assertRaises(ValueError):
                project_signal(changed_packet, source, lesson, media, lib)
        finally:
            lib.close()

    def test_candidate_cannot_publish_and_export_marks_missing_consumer(self):
        script = ROOT / "scripts/publish-concept-library.py"
        blocked = subprocess.run(
            [
                sys.executable,
                "-X",
                "utf8",
                "-B",
                str(script),
                "--web-root",
                "missing",
                "--contract",
                "candidate-signal",
                "--apply",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(blocked.returncode, 0)
        self.assertIn("export-only", blocked.stderr)
        with tempfile.TemporaryDirectory() as directory:
            exported = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    "-B",
                    str(script),
                    "--web-root",
                    WEB,
                    "--concepts",
                    "C-AM-01",
                    "--contract",
                    "candidate-signal",
                    "--output",
                    directory,
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(exported.returncode, 0, exported.stderr)
            report = json.loads(exported.stdout)[0]
            self.assertFalse(report["hasAppCompatibleMedia"])
            self.assertTrue(report["hasCandidateMedia"])
            self.assertEqual(report["cloudStatus"], "not_written")
            self.assertTrue(
                (
                    Path(directory) / "concept-media-signal-candidate.schema.json"
                ).is_file()
            )
            self.assertEqual(
                json.loads(
                    (
                        Path(directory) / "concept-media-signal-candidate.schema.json"
                    ).read_text(encoding="utf-8")
                ),
                json.loads(
                    (
                        ROOT / "contracts/concept-media-signal-candidate.schema.json"
                    ).read_text(encoding="utf-8")
                ),
            )


if __name__ == "__main__":
    unittest.main()
