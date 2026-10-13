# Learner-profile prompt v2: bounded experiment

This text file is the exact sequence of system-instruction text parts used in the v2 trial, joined by blank lines for copying. The accompanying API request also contains a stage task, the original source/glossary, a learner profile, per-sentence term counts, the validated draft for stage two, and the existing strict response JSON schema. The CLI's default prompt and input schema have not been changed to use this experiment automatically.

## Profile and scope

English self-reported confidence 5/10, Odia 7/10; Odia-led conversational explanations. Proposed retained English phrases: voltage-controlled oscillator, direct frequency modulation, control input, ideal linear model, VCO sensitivity, message voltage. These are preferences for a hypothetical learner, not measured word familiarity or a language percentage. This prompt still contains VCO-specific examples and sentence rules; it is not a universal production localization prompt.

## Controlled iterations

Same model (`gemini-3.5-flash-lite`), source, schema, and raw-output validators. No response text repair, span normalization, or weakening of validators.

| Version | One prompt change | Actual outcome |
| --- | --- | --- |
| v0 | Exact prior profile prompt, reproduced by request hash | Translation rejected: VCO duplicated in s4 |
| v1 | Added hard positive/negative examples | Translation passed; mixed rejected: ordinary English `the carrier` inside an Odia span |
| v2 | Clarified language labels for every Latin word, including helpers | Translation passed; mixed request returned HTTP 503 |
| v2 held-out | No prompt change; new predeclared input | Both raw stages passed all automated checks |
| v2 resume | No prompt change; reused accepted translation and retried the identical mixed request once after 319.1 seconds | Mixed passed; original VCO flow completed |

Eight API requests total: seven returned structured candidate responses and one returned HTTP 503. A local scratch-helper import-name error was fixed before any retry request was sent. No further network retries or prompt changes followed the held-out result.

The held-out input was defined before this iteration and was not used in examples or edited after evaluation. It is an assistant-authored synthetic evaluation paragraph, not a verified textbook passage or measured VCO result. Values and negation exercise preservation boundaries; scientific/native-Odia review remains pending. Two small cases do not establish a production compliance rate.

## What automated validation establishes

Original IDs/order, declared fields, language spans and writing systems, exact glossary-term counts (including zero counts), protected literals/displayed numbers, required spoken expansions, and exact additional phrase counts in display and speech. Raw validation gates each stage before the next call. Transport checks require one complete STOP candidate and JSON. Secrets and existing outputs are protected by the existing adapter/CLI checks.

These checks do not establish scientific equivalence, negation/ideal-model fidelity, Odia grammar, readability for 5/10 or 7/10 ratings, learner comprehension, or audio quality. A synthetic negative control added `This always holds in every real circuit.` to a fixture sentence. It passed the preservation validator despite contradicting the source's bounded ideal-model scope. Qualified semantic/native review is still required; a model's self-check is not that review.

## Reproduction and continuity

The trial uses the existing `GeminiGenerator`, `run_pipeline`, `validate_stage`, and strict response schema. Ignored artifacts in `work/prompt-hardening/` retain every request, raw response, call hash/version/usage, result, and evaluation summary. The successful VCO result is `labels-v2-resume.result.json`; held-out result is `heldout-v2.result.json`. The local experimental harness is `work/harden-profile-prompt.py`, with its single-retry helper `work/resume-hardened-profile.py`.

The repository holds the exact prompt text and held-out input. The user later authorized publishing the session work; the [evidence archive](../evidence/2026-10-13/README.md) preserves generated results, requests/failures and historical scratch-driver source without credential values. The original ignored `work/` layout does not automatically transfer and archived drivers are reference code, not a supported CLI. The original complete baseline is preserved there as `vco-live.json`.

Subsequent user decision: the translation/audio pipeline direction is accepted, and the future FastAPI endpoint must take two tunable Odia/English proficiency numbers out of 10. See the [chosen pipeline](../../../docs/decisions/0001-mixed-language-audio-pipeline.md) and [architecture assessment](../../../docs/architecture/mixed-language-fastapi.md). This v2 experiment remains unchanged and VCO-specific; arbitrary ratings and paragraph types still require generalization/evaluation. Preserve the prior default as rollback. The user requested documentation/design, not backend building. TTS and the private listening Site were later separate authorized trials, not evidence from these prompt iterations.
