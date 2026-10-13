# Kiki backend starter

This starter carries the Design-Thinking product context and BB8 into a separate backend repository. It does not contain a running backend yet.

1. Follow [CONTEXT-BOOT.md](CONTEXT-BOOT.md) to load context, report readiness, and wait for the user's thoughts.
2. Read [SETUP.md](SETUP.md) for the context-only startup prompt and later environment guidance.
3. Read [context/README.md](context/README.md) for source precedence and the reading order.
4. Read [the seven prototype directions](context/design-thinking/docs/prototypes/backend-prototype-directions.md).
5. Run `python scripts/verify-context.py` to check the imported source snapshot if command access is available.

`context/design-thinking/SOURCE.json` records the source repo, exact commit, and SHA-256 for every copied product file. `STARTER-MANIFEST.json` describes the starter/handoff baseline, refreshed when commit identities were corrected; it is not a permanent freeze on new backend code. The source snapshot is a traceable baseline, while backend decisions and progress belong in this repository.

Importing the source files alone does not establish credentials, API access, native BB8 activation, generated media or a real-tool connection. Subsequent authorized trials have generated live mixed-language scripts and actual speech; graphics and Simulink integration remain unimplemented.

The user has chosen the [English-to-mixed-language and audio pipeline](docs/decisions/0001-mixed-language-audio-pipeline.md) after listening to its prototype. Reuse the [existing text and speech modules](prototypes/mixed_script/README.md). Scientific/native-Odia review and generalization of the learner-profile prompt remain pending; the longer sample is a disclosed draft.

FastAPI is the selected future backend framework. The [scalability and WPM assessment](docs/architecture/mixed-language-fastapi.md) is a design proposal, not a running API. Every future generation request must include independent Odia and English proficiency settings out of 10. The user explicitly requested **no backend building yet**.

The next parallel session should use the [graphics, pointing and annotation handoff](docs/handoffs/graphics-and-annotation.md), which separates generated-content annotation from live-screen guidance and records the audio-alignment dependency. The user authorized publishing the session work; fetch current main and verify these files rather than stopping at the original pipeline commit. A [versioned evidence archive](prototypes/mixed_script/evidence/2026-10-13/README.md) preserves actual generated scripts, recordings and trial records; original scratch paths remain ignored.
