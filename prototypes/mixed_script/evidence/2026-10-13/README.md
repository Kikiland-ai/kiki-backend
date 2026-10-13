# Session evidence archive — 13 October 2026

Published at the user's explicit request to commit/push the session's work. These are preserved experimental records and real audio, not production fixtures or a scientific/native-Odia sign-off. No new provider calls were made to create this archive. `manifest.json` records original runtime paths, sizes and SHA-256 hashes. Six historical text files with original trailing whitespace are stored losslessly as `.gz` files; their decompressed bytes match the original payload hashes. This preserves exact prompt/driver content without changing whitespace checks for source files.

## Read/listen first

- [Completed original baseline](vco-live.json).
- [Completed v2 VCO text](prompt-hardening/labels-v2-resume.result.json), [held-out text](prompt-hardening/heldout-v2.result.json) and [evaluation report](prompt-hardening/evaluation-report.json).
- [Longer English input](longer-vco-tts/english-input.txt), [generated translation draft](longer-vco-tts/translation.draft.txt), [exact speech text](longer-vco-tts/speech-ready.draft.txt) and [combined draft result](longer-vco-tts/bundle.draft.result.json).
- [104.8-second MP3](longer-vco-tts/speech-draft.mp3), [original WAV](longer-vco-tts/speech-draft.wav) and [audio manifest](longer-vco-tts/audio.manifest.draft.json).
- [51.68-second completed-text pilot MP3](vco-tts-smoke/speech.mp3) and [pilot manifest](vco-tts-smoke/audio.manifest.json).
- [Model-access investigation](gemini-access-investigation.json).
- [Offline listening page](listening-site/index.html) and [private Site publication record](listening-site/deployment-result.json). Download the page and neighboring MP3 to open it locally; the hosting manifest is a reference to the separately published Site.

The longer result explicitly has `mixed: null`, a span-label-only repair preserving every display character, three phrase-count warnings and a 503-blocked refinement. The recording was synthesized from that translation draft. The user accepted the pipeline direction after listening; formal meaning/native-Odia/pronunciation review remains pending. Audio duration is measured; sentence/word timing is absent.

## Preserved experiments

Requests, raw candidates, failure summaries, prompt revisions and the deliberately unsupported semantic negative control are retained. The negative control is labelled invalid teaching content even though the preservation validator accepted it. Earlier selected-sentence comparisons are not a single completed generated paragraph.

Historical Python drivers are retained as reference source (decompress `.gz` records first), including their original hard-coded `work/` dependencies and run IDs. They are **not a supported CLI**, and several execute provider calls when run. Replaying requires restoring the applicable files into a fresh ignored `work/` layout, inspecting dependencies/output guards and explicit trial authorization. Do not run them merely to load context, and do not overwrite archived or original outputs.

The `work/` originals remain ignored. Credential values, secret files, Git authentication, transient caches and private publication credentials are excluded. The Site itself uses a separate repository; its source revision and deployment IDs are captured here, while the backend's pipeline/architecture documentation remains authoritative.
