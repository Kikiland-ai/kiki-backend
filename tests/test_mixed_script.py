"""Offline boundary tests; mocked HTTP is not a live Gemini acceptance trial."""
import copy
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import urllib.error

from prototypes.mixed_script.pipeline import (
    DEFAULT_FIXTURE, DEFAULT_INPUT, FixtureGenerator, GeminiGenerator, PipelineError,
    make_request, read_json, run_pipeline, save_result, validate_input, validate_stage,
)


class MixedScriptTests(unittest.TestCase):
    def setUp(self):
        self.source = read_json(DEFAULT_INPUT)
        self.fixture = read_json(DEFAULT_FIXTURE)
        self.glossary = validate_input(self.source)

    def validate_mixed(self, candidate):
        return validate_stage(self.source, candidate, self.glossary)

    def test_complete_fixture_preserves_provenance_and_source_ids(self):
        generator = FixtureGenerator(self.fixture)
        result = run_pipeline(self.source, generator)
        self.assertEqual([c["stage"] for c in generator.calls], ["translation", "mixed"])
        self.assertEqual([s["id"] for s in result["mixed"]["sentences"]], ["s1", "s2", "s3", "s4"])
        self.assertEqual(result["provenance"]["mode"], "fixture")
        self.assertIsNone(result["provenance"]["model"])
        self.assertEqual(result["validation"]["meaning_review"], "pending")
        self.assertEqual(result["validation"]["native_Odia_review"], "pending")
        self.assertEqual(result["audio"]["status"], "not_generated")
        self.assertIsNone(result["audio"]["timing_cues"])
        self.assertIn("f_i(t) = f_c + K_v m(t)", result["paragraph"])
        self.assertIn("hertz per volt", result["speech_script"])

    def test_mix_request_retains_original_and_validated_translation(self):
        translation = validate_stage(self.source, self.fixture["translation"], self.glossary)
        request = make_request(self.source, "mixed", translation)
        data = json.loads(request["contents"][0]["parts"][0]["text"])
        self.assertEqual(data["original"], self.source)
        self.assertEqual(data["draft_translation"], translation)

    def test_reordered_ids_are_rejected(self):
        candidate = copy.deepcopy(self.fixture["mixed"])
        candidate["sentences"][0], candidate["sentences"][1] = candidate["sentences"][1], candidate["sentences"][0]
        with self.assertRaisesRegex(PipelineError, "IDs"):
            self.validate_mixed(candidate)

    def test_missing_canonical_term_is_rejected(self):
        candidate = copy.deepcopy(self.fixture["mixed"])
        candidate["sentences"][0]["spans"][2]["text"] = "oscillator"
        with self.assertRaisesRegex(PipelineError, "technical term"):
            self.validate_mixed(candidate)

    def test_changed_equation_is_rejected(self):
        candidate = copy.deepcopy(self.fixture["mixed"])
        span = candidate["sentences"][2]["spans"][3]
        span["text"] = span["text"].replace("+", "-")
        with self.assertRaisesRegex(PipelineError, "formula"):
            self.validate_mixed(candidate)

    def test_new_numeric_claim_is_rejected(self):
        candidate = copy.deepcopy(self.fixture["mixed"])
        candidate["sentences"][0]["spans"][0]["text"] += " 100"
        with self.assertRaisesRegex(PipelineError, "Numeric"):
            self.validate_mixed(candidate)

    def test_romanized_odia_is_rejected(self):
        candidate = copy.deepcopy(self.fixture["mixed"])
        for span in candidate["sentences"][0]["spans"]:
            if span["language"] == "or":
                span["text"] = " ra "
        with self.assertRaisesRegex(PipelineError, "Latin text"):
            self.validate_mixed(candidate)

    def test_missing_spoken_acronym_expansion_is_rejected(self):
        candidate = copy.deepcopy(self.fixture["mixed"])
        sentence = candidate["sentences"][0]
        sentence["speech_text"] = sentence["speech_text"].replace("V C O", "VCO")
        with self.assertRaisesRegex(PipelineError, "spoken term"):
            self.validate_mixed(candidate)

    def test_hindi_in_speech_is_rejected(self):
        candidate = copy.deepcopy(self.fixture["mixed"])
        candidate["sentences"][0]["speech_text"] += " नमस्ते"
        with self.assertRaisesRegex(PipelineError, "unsupported writing"):
            self.validate_mixed(candidate)

    def test_unknown_input_term_reference_is_rejected_before_request(self):
        self.source["sentences"][0]["term_ids"].append("not-in-glossary")
        generator = FixtureGenerator(self.fixture)
        with self.assertRaisesRegex(PipelineError, "term references"):
            run_pipeline(self.source, generator)
        self.assertEqual(generator.calls, [])

    def test_invalid_translation_stops_before_mix(self):
        self.fixture["translation"]["sentences"][0]["id"] = "changed"
        generator = FixtureGenerator(self.fixture)
        with self.assertRaises(PipelineError):
            run_pipeline(self.source, generator)
        self.assertEqual([c["stage"] for c in generator.calls], ["translation"])

    def test_display_and_speech_have_different_representations_of_value(self):
        # Numeric speech expansion is intentional; changed displayed values are not.
        self.source["sentences"][0]["english"] += " The example value is 0.7 V."
        self.source["sentences"][0]["literals"] = [{"text": "0.7 V", "spoken": "zero point seven volts"}]
        candidate = copy.deepcopy(self.fixture["mixed"])
        candidate["sentences"][0]["spans"].extend([
            {"language": "or", "text": " ଉଦାହରଣ: "},
            {"language": "en", "text": "0.7 V"},
        ])
        candidate["sentences"][0]["speech_text"] += " ଉଦାହରଣ: zero point seven volts।"
        self.validate_mixed(candidate)
        candidate["sentences"][0]["spans"][-1]["text"] = "7.0 V"
        with self.assertRaises(PipelineError):
            self.validate_mixed(candidate)

    def test_gemini_request_uses_header_and_parses_two_transport_responses(self):
        requests = []
        stages = iter([self.fixture["translation"], self.fixture["mixed"]])

        def opener(request, timeout):
            requests.append(request)
            body = {"candidates": [{"finishReason": "STOP", "content": {"parts": [
                {"thought": True, "text": "not candidate text"},
                {"text": json.dumps(next(stages), ensure_ascii=False)},
            ]}}], "modelVersion": "test-model-version", "usageMetadata": {"totalTokenCount": 10}}
            return io.BytesIO(json.dumps(body).encode())

        result = run_pipeline(self.source, GeminiGenerator("test-key-not-a-real-secret", opener=opener))
        self.assertEqual(len(requests), 2)
        for request in requests:
            self.assertNotIn("test-key-not-a-real-secret", request.full_url)
            self.assertNotIn(b"test-key-not-a-real-secret", request.data)
            self.assertEqual(request.get_header("X-goog-api-key"), "test-key-not-a-real-secret")
        self.assertEqual(result["provenance"]["calls"][0]["usage"]["totalTokenCount"], 10)

    def test_truncated_provider_response_is_rejected(self):
        def opener(request, timeout):
            return io.BytesIO(json.dumps({"candidates": [{"finishReason": "MAX_TOKENS"}]}).encode())
        with self.assertRaisesRegex(PipelineError, "truncated"):
            run_pipeline(self.source, GeminiGenerator("test-key", opener=opener))

    def test_http_errors_do_not_expose_credentials_or_response_body(self):
        def opener(request, timeout):
            raise urllib.error.HTTPError(request.full_url, 403, "test-secret-in-reason", {},
                                         io.BytesIO(b"test-secret-in-body"))
        with self.assertRaises(PipelineError) as caught:
            run_pipeline(self.source, GeminiGenerator("test-secret-in-key", opener=opener))
        self.assertIn("403", str(caught.exception))
        self.assertNotIn("test-secret", str(caught.exception))

    def test_missing_key_fails_before_network(self):
        with self.assertRaisesRegex(PipelineError, "GEMINI_API_KEY"):
            GeminiGenerator("")

    def test_result_does_not_overwrite_existing_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "result.json"
            path.write_text("keep this")
            with self.assertRaisesRegex(PipelineError, "already exists"):
                save_result({}, path)
            self.assertEqual(path.read_text(), "keep this")

    def test_cli_fails_before_provider_call_when_output_exists(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "result.json"
            path.write_text("keep this")
            result = subprocess.run([sys.executable, "-B", str(root / "scripts/generate-mixed-script.py"),
                                     "--mode", "gemini", "--output", str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("already exists", result.stderr)
            self.assertEqual(path.read_text(), "keep this")


if __name__ == "__main__":
    unittest.main()
