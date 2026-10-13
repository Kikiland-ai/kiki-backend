# Mixed-language script baseline

One small, dependency-free Python 3.12 text CLI with a separate speech connector. The user accepted this as the [chosen translation/audio pipeline](../../docs/decisions/0001-mixed-language-audio-pipeline.md). FastAPI is the selected future backend framework; [endpoint/scaling design](../../docs/architecture/mixed-language-fastapi.md) is documented, and implementation remains paused at the user's instruction.

The future endpoint requires two independent student-provided proficiency settings out of 10. The current shared CLI still has one fixed mix setting; the 5/7 profile experiment has not been generalized or wired into it. Acceptance of the pipeline direction does not certify every sample's scientific/Odia equivalence.

It follows the approved two-stage flow:

1. Translate a cited English paragraph into Odia-led text, retaining English glossary terms.
2. Refine it into natural mixed Odia/English teaching language, checking against the original English.

The baseline uses native **Odia script**, with English technical terms in Latin letters. It does not generate Romanized Odia or select language support for the student. Only one mix setting is supported initially.

## Input and provenance

`fixtures/mixed-script/vco.input.json` contains four stable sentence IDs, source references, a draft glossary, and protected symbols/formulas with spoken expansions. The English paragraph is an assistant-authored adaptation of the cited references, not a verbatim source excerpt. Its affine VCO equation is an ideal linear-model assumption; it needs domain review. No uploaded textbook/lecture source was available in this checkout.

The glossary's Odia meanings and pronunciation guides are **unreviewed drafts**. They inform the generator but are not automatically appended to the narration.

`vco.generated.fixture.json` supplies assistant-authored translation/mix responses for offline checks. A fixture run makes no model calls and always records `mode: fixture`, `provider: none`, and pending review. It cannot establish Gemini's translation quality.

## Run without credentials

From the repository root:

```sh
python -B scripts/generate-mixed-script.py --mode fixture
python -B -m unittest discover -s tests -v
```

## Run with Gemini

Add `GEMINI_API_KEY` through the attached cloud environment's persistent **Secrets** settings. Reuse the same saved environment configuration in future sessions. These credentials do not automatically follow unrelated environments or chats. Do not put keys into chat, source files, command arguments, or Git.

Allow outbound HTTPS to `generativelanguage.googleapis.com` through environment settings. The CLI uses the inherited HTTPS proxy and CA trust. It does not alter network policy or bypass a blocked destination.

```sh
python -B scripts/generate-mixed-script.py --mode gemini --output /absolute/existing-directory/vco-live.json
```

The current CLI default is `gemini-3.8-flash`; it returned HTTP 503 in this runtime's access probe. Completed text trials used an explicit `gemini-3.5-flash-lite` override, which subsequently also experienced capacity failures. Override with `--model` or the non-secret `GEMINI_TEXT_MODEL` variable only after checking actual account/model availability. Catalog listing alone does not prove generation access. The adapter makes **two** `generateContent` requests, without automatic retries. If the first result fails validation, the second request is not sent. A successful response requires a complete `STOP` candidate containing JSON, not a truncated answer.

The key is sent as an HTTP header. Response bodies, request headers, and raw transport exceptions are not printed. `urllib` uses session proxy and TLS settings. The CLI reads credentials from the process environment; it does not automatically load `.env`.

Gemini Developer API keys and Google Cloud authentication are different. This first adapter uses the Developer API key only. A later Cloud TTS/Vertex/Enterprise connector should use a configured Google Cloud identity/Application Default Credentials. A managed outbound identity or Secret Manager with workload identity is preferable to committing or copying service-account keys. Project/region/model names are non-secret configuration, not authentication.

## What is actually checked

- Sentence count, IDs/order, exact response fields, and language span labels.
- Presence of native Odia script; Latin letters are kept in English spans.
- Protected English glossary terms retain spelling, case, and occurrence counts per sentence.
- Protected formulas/symbols/units are retained verbatim; displayed numeric values cannot be changed or added.
- The speech-ready text includes the supplied acronym/formula/unit expansions.

These checks do **not** prove scientific equivalence, preservation of negation/qualifiers, or natural Odia. The prompts request these behaviors, but outputs retain `meaning_review: pending` and `native_Odia_review: pending` until a person checks them.

The text CLI result includes source/glossary data, input and request hashes, prompt/model provenance, separate translation and mixed stages, display paragraphs, and a plain speech script. Its audio status remains `not_generated`; the separate speech connector produces audio and its own manifest. No timing cues are invented. CLI output files are created only after both text stages validate, and existing files are preserved.

## Bounded speech trial

The separate `speech.py` adapter sends an exact speech-ready transcript to Gemini's Interactions REST API. It supports `gemini-3.8-flash-tts` and `gemini-3.8-flash-lite-tts`, with a prebuilt voice (Kore by default). Narration style is passed separately from the transcript. Authentication and proxy/TLS behavior follow the text adapter; there are no automatic retries. This module is not wired into the text CLI.

It returns WAV bytes and a provenance manifest after checking readable, complete, non-silent 24 kHz mono 16-bit PCM. Clip duration comes from the actual frame count. These checks do not prove pronunciation, spoken fidelity or intelligibility. The manifest leaves native-Odia/pronunciation review pending and supplies no sentence/word timing cues.

The user-authorized longer trial is saved in ignored `work/longer-vco-tts/`: eight sentences, 151 English words, numerical ideal-model examples, a generated translation draft and a real 104.8-second Kore recording using `gemini-3.8-flash-lite-tts`. Text-model capacity failures blocked final mixed refinement. `script.draft.result.json` therefore has `mixed: null`; label-only repair and three preferred-phrase warnings are disclosed. `bundle.draft.result.json`, `speech-draft.wav`, `speech-draft.mp3` and `audio.manifest.draft.json` preserve the listening trial separately from accepted final output. The later user-authorized [evidence archive](evidence/2026-10-13/README.md) preserves copies in Git for another runtime, alongside completed original/held-out results and the speech pilot.

The user listened through the owner-private [Sites player](https://kiki-vco-listening-draft.woodsycarp256.chatgpt.site) and accepted the direction. Formal scientific/native-Odia/pronunciation review remains separate. Its Site source/deployment does not constitute a deployed backend.

The current narration style is fixed. A future WPM target would be a measured soft pacing request, not a verified numeric provider setting; see the [WPM assessment](../../docs/architecture/mixed-language-fastapi.md#wpm-and-playback-speed). No pace trial or speed control was added. See [the active plan](../../docs/plans/active.md) for actual checks and continuation.

## Next evidence

Compare every sentence with the English source, resolve the longer draft's phrase/meaning concerns, and have an Odia speaker listen to the actual recording. Complete mixed refinement before accepting this longer script. Speech generation does not imply approval of the transcript or spoken result.

## Learner-profile prompt experiment

The user-supplied BB8 `prompt-design-engineering` skill guided a bounded English-5/10/Odia-7/10 prompt trial. The [exact v2 system instructions](prompts/learner-profile-v2.txt) and [evaluation notes](prompts/README.md) are saved for review. Both the original VCO case and a predeclared synthetic held-out case passed raw automated checks with `gemini-3.5-flash-lite`; scientific/native-Odia review remains pending. The CLI default prompt/input contract has not been changed to select this experimental profile automatically.

Provider references:

- [Gemini 3.8 Flash](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash)
- [GenerateContent structured output](https://ai.google.dev/gemini-api/docs/generate-content/structured-output)
- [Gemini REST API](https://ai.google.dev/api/generate-content)
- [Gemini speech generation](https://ai.google.dev/gemini-api/docs/speech-generation)
- [Gemini 3.8 Flash Lite TTS](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash-lite-tts)
