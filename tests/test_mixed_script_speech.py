"""Mocked audio boundary tests; these do not establish actual voice quality."""
import base64
import io
import json
import struct
import unittest
import urllib.error
import wave

from prototypes.mixed_script.pipeline import PipelineError
from prototypes.mixed_script.speech import GeminiSpeechGenerator, inspect_wav


def wav_bytes(silence=False):
    stream = io.BytesIO()
    with wave.open(stream, "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(24000)
        output.writeframes(struct.pack("<hhhh", 0, 0, 0, 0) if silence else struct.pack("<hhhh", 0, 1000, -1000, 0))
    return stream.getvalue()


def envelope(data=None, status="completed"):
    return {"status": status, "model": "test-speech-model", "steps": [
        {"type": "model_output", "content": [{"type": "audio", "mime_type": "audio/wav",
                                               "data": base64.b64encode(data or wav_bytes()).decode()}]},
    ], "usage": {"total_tokens": 10}}


class SpeechTests(unittest.TestCase):
    def test_exact_transcript_and_style_are_separate_and_key_is_only_in_header(self):
        calls = []
        transcript = "ଏଠାରେ V C O ଅଛି।"

        def opener(request, timeout):
            calls.append(request)
            payload = json.loads(request.data)
            text = payload["input"][0]["content"][0]
            self.assertEqual(text["text"], transcript)
            self.assertEqual(text["annotations"][0]["type"], "speech_metadata")
            self.assertNotIn("fixture-key", request.full_url)
            self.assertNotIn(b"fixture-key", request.data)
            self.assertEqual(request.get_header("X-goog-api-key"), "fixture-key")
            return io.BytesIO(json.dumps(envelope()).encode())

        data, metadata = GeminiSpeechGenerator("fixture-key", opener=opener).generate(transcript)
        self.assertEqual(data, wav_bytes())
        self.assertEqual(len(calls), 1)
        self.assertAlmostEqual(metadata["audio"]["duration_seconds"], 4 / 24000)
        self.assertIsNone(metadata["timing_cues"])
        self.assertEqual(metadata["review"]["native_Odia"], "pending")

    def test_incomplete_interaction_is_rejected_even_with_audio(self):
        opener = lambda request, timeout: io.BytesIO(json.dumps(envelope(status="in_progress")).encode())
        with self.assertRaisesRegex(PipelineError, "completed"):
            GeminiSpeechGenerator("fixture-key", opener=opener).generate("test transcript")

    def test_malformed_audio_encoding_is_rejected(self):
        response = envelope()
        response["steps"][0]["content"][0]["data"] = "not valid base64!"
        opener = lambda request, timeout: io.BytesIO(json.dumps(response).encode())
        with self.assertRaisesRegex(PipelineError, "encoded audio"):
            GeminiSpeechGenerator("fixture-key", opener=opener).generate("test transcript")

    def test_http_error_body_headers_and_key_are_not_exposed(self):
        def opener(request, timeout):
            raise urllib.error.HTTPError(request.full_url, 429, "secret-reason", {}, io.BytesIO(b"secret-body"))
        with self.assertRaises(PipelineError) as caught:
            GeminiSpeechGenerator("secret-key", opener=opener).generate("test transcript")
        self.assertIn("429", str(caught.exception))
        self.assertNotIn("secret", str(caught.exception))

    def test_unreadable_or_truncated_wav_is_rejected(self):
        for data in (b"not WAV", wav_bytes()[:-2]):
            with self.subTest(data=data), self.assertRaises(PipelineError):
                inspect_wav(data)

    def test_silent_audio_is_rejected(self):
        with self.assertRaisesRegex(PipelineError, "silence"):
            inspect_wav(wav_bytes(silence=True))

    def test_missing_key_or_unsupported_model_fail_before_network(self):
        with self.assertRaises(PipelineError):
            GeminiSpeechGenerator("")
        with self.assertRaises(PipelineError):
            GeminiSpeechGenerator("fixture-key", model="gemini-2.5-flash-preview-tts")


if __name__ == "__main__":
    unittest.main()
