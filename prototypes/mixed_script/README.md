# Mixed-language script baseline

One small, dependency-free Python 3.12 CLI. The actual application/backend stack remains a later decision.

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

The default text model is `gemini-3.8-flash`, documented as stable when this baseline was prepared on 13 October 2026. Override it with `--model` or the non-secret `GEMINI_TEXT_MODEL` environment variable if account availability changes. The adapter makes **two** `generateContent` requests, without automatic retries. If the first result fails validation, the second request is not sent. A successful response requires a complete `STOP` candidate containing JSON, not a truncated answer.

The key is sent as an HTTP header. Response bodies, request headers, and raw transport exceptions are not printed. `urllib` uses session proxy and TLS settings. The CLI reads credentials from the process environment; it does not automatically load `.env`.

Gemini Developer API keys and Google Cloud authentication are different. This first adapter uses the Developer API key only. A later Cloud TTS/Vertex/Enterprise connector should use a configured Google Cloud identity/Application Default Credentials. A managed outbound identity or Secret Manager with workload identity is preferable to committing or copying service-account keys. Project/region/model names are non-secret configuration, not authentication.

## What is actually checked

- Sentence count, IDs/order, exact response fields, and language span labels.
- Presence of native Odia script; Latin letters are kept in English spans.
- Protected English glossary terms retain spelling, case, and occurrence counts per sentence.
- Protected formulas/symbols/units are retained verbatim; displayed numeric values cannot be changed or added.
- The speech-ready text includes the supplied acronym/formula/unit expansions.

These checks do **not** prove scientific equivalence, preservation of negation/qualifiers, or natural Odia. The prompts request these behaviors, but outputs retain `meaning_review: pending` and `native_Odia_review: pending` until a person checks them.

The result includes source/glossary data, input and request hashes, prompt/model provenance, separate translation and mixed stages, display paragraphs, and a plain speech script. It contains no synthesized audio or invented timing cues. Output files are created only after both stages validate, and existing files are preserved.

## Next evidence

Run once with the configured key; compare every sentence with the English source and have an Odia speaker review it. Then send the accepted speech script to a selected TTS connector and inspect actual audio before adding playback/timing.

Provider references:

- [Gemini 3.8 Flash](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash)
- [GenerateContent structured output](https://ai.google.dev/gemini-api/docs/generate-content/structured-output)
- [Gemini REST API](https://ai.google.dev/api/generate-content)
