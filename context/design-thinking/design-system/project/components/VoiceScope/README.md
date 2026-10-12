# VoiceScope

Hold-to-speak recording shown as a live waveform on an oscilloscope screen, then playback, transcript and one fix.

**Consumer provides:** optional `prompt` (a sentence starter), `transcript` (node), `feedback` (one praise plus one fix), `defaultState`. The preview simulates audio; the app records with MediaRecorder and transcribes with Gemini.

- Do: keep recordings at 30 s or less and play them back automatically.
- Don't: grade pronunciation in the demo. Always offer typing as a fallback.
