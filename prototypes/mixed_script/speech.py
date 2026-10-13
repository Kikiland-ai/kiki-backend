"""Bounded Gemini 3.8 TTS trial through the documented Interactions REST API.

Uses the inherited proxy and TLS trust. Audio generation is not pronunciation,
transcript-fidelity, or timing-alignment acceptance.
"""
import array
import base64
import binascii
import hashlib
import io
import json
import math
import re
import sys
import urllib.error
import urllib.request
import wave

from .pipeline import API_ORIGIN, PipelineError, digest, require_text


DEFAULT_SPEECH_MODEL = "gemini-3.8-flash-tts"
DEFAULT_VOICE = "Kore"


def inspect_wav(data):
    try:
        with wave.open(io.BytesIO(data), "rb") as stream:
            rate, channels, width = stream.getframerate(), stream.getnchannels(), stream.getsampwidth()
            count, compression = stream.getnframes(), stream.getcomptype()
            if rate != 24000 or channels != 1 or width != 2 or compression != "NONE":
                raise PipelineError("Expected uncompressed 24 kHz mono 16-bit WAV audio.")
            if not 0 < count <= rate * 600:
                raise PipelineError("Audio duration is empty or exceeds this trial's limit.")
            frames = stream.readframes(count)
    except (wave.Error, EOFError, OSError):
        raise PipelineError("Provider audio is not a readable WAV file.") from None
    if len(frames) != count * channels * width:
        raise PipelineError("Provider WAV audio is truncated.")
    samples = array.array("h", frames)
    if sys.byteorder != "little":
        samples.byteswap()
    peak = max(abs(sample) for sample in samples)
    if peak == 0:
        raise PipelineError("Provider WAV contains only silence.")
    return {"format": "WAV PCM", "sample_rate_hz": rate, "channels": channels,
            "sample_width_bytes": width, "frames": count, "duration_seconds": count / rate,
            "peak_pcm": peak, "rms_pcm": math.sqrt(sum(s * s for s in samples) / count),
            "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


class GeminiSpeechGenerator:
    def __init__(self, api_key, model=DEFAULT_SPEECH_MODEL, voice=DEFAULT_VOICE,
                 timeout=180, opener=None):
        if not isinstance(api_key, str) or not api_key.strip():
            raise PipelineError("Set GEMINI_API_KEY in the process environment before speech generation.")
        if model not in ("gemini-3.8-flash-tts", "gemini-3.8-flash-lite-tts"):
            raise PipelineError("This speech adapter supports the documented Gemini 3.8 TTS models.")
        if not isinstance(voice, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,79}", voice):
            raise PipelineError("Invalid prebuilt voice name.")
        self.api_key, self.model, self.voice = api_key, model, voice
        self.timeout, self.opener = timeout, opener or urllib.request.urlopen

    def make_request(self, speech_script):
        require_text(speech_script, "speech script")
        return {
            "model": self.model,
            "input": [{"type": "user_input", "content": [{
                "type": "text", "text": speech_script,
                "annotations": [{"type": "speech_metadata",
                                 "style": "clear, patient Odia-English teaching narration"}],
            }]}],
            "response_format": {"type": "audio", "mime_type": "audio/wav", "sample_rate": 24000},
            "generation_config": {"speech_config": [{"voice": self.voice}]},
        }

    def generate(self, speech_script):
        payload = self.make_request(speech_script)
        request = urllib.request.Request(API_ORIGIN + "/v1beta/interactions", method="POST",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json", "x-goog-api-key": self.api_key})
        try:
            with self.opener(request, timeout=self.timeout) as response:
                raw = response.read(32_000_001)
            if len(raw) > 32_000_000:
                raise PipelineError("Speech response exceeded this trial's size limit.")
            result = json.loads(raw)
        except urllib.error.HTTPError as error:
            raise PipelineError(f"Gemini TTS HTTP {error.code}. No automatic retry was made.") from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise PipelineError("Cannot reach Gemini TTS; check allowed host and inherited proxy/TLS setup.") from None
        except (json.JSONDecodeError, UnicodeError):
            raise PipelineError("Gemini TTS returned invalid JSON.") from None
        if not isinstance(result, dict) or result.get("status") != "completed":
            raise PipelineError("Gemini TTS did not return a completed interaction.")
        steps = result.get("steps")
        if not isinstance(steps, list):
            raise PipelineError("Gemini TTS returned no documented output steps.")
        blocks = []
        for step in steps:
            if not isinstance(step, dict) or step.get("type") != "model_output":
                continue
            content = step.get("content")
            if not isinstance(content, list):
                raise PipelineError("Gemini TTS returned invalid model output content.")
            blocks.extend(block for block in content if isinstance(block, dict) and block.get("type") == "audio")
        if len(blocks) != 1 or blocks[0].get("mime_type") != "audio/wav":
            raise PipelineError("Expected one complete audio/wav output block.")
        encoded = blocks[0].get("data")
        if not isinstance(encoded, str):
            raise PipelineError("Gemini TTS returned no encoded audio data.")
        try:
            data = base64.b64decode(encoded, validate=True)
        except (ValueError, binascii.Error):
            raise PipelineError("Gemini TTS returned malformed encoded audio.") from None
        audio = inspect_wav(data)
        usage = result.get("usage", {})
        safe_usage = {k: v for k, v in usage.items() if isinstance(v, int)} if isinstance(usage, dict) else {}
        metadata = {
            "schema": "mixed-script-audio-trial/v1", "status": "generated",
            "provider": "Gemini Developer API", "api": "Interactions REST v1beta",
            "model": self.model, "returned_model": result.get("model"), "voice": self.voice,
            "request_sha256": digest(payload),
            "speech_script_sha256": hashlib.sha256(speech_script.encode("utf-8")).hexdigest(),
            "usage": safe_usage, "audio": audio,
            "timing_cues": None, "alignment_status": "not_performed",
            "review": {"pronunciation": "pending", "native_Odia": "pending", "spoken_fidelity": "pending"},
        }
        return data, metadata
