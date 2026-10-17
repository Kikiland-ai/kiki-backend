# Current unified prototype setup

This branch adds a runnable single-process FastAPI backend. Install `prototypes/screen_capture/requirements.txt`, then run `python -B -m prototypes.backend --port 8765 --data-dir work/backend`. Remote access still requires actual authenticated HTTPS Python hosting; the live Site remains Worker/D1 until the bridge is deliberately activated. See [frontend handoff](docs/handoffs/frontend-api.md) and [deployment setup](deploy/fastapi/README.md). The historical context-only setup below does not describe current endpoint availability.

# Start backend work without losing product context

This repository contains working mixed-language text/speech prototypes and a chosen FastAPI/worker architecture, but no running API. The [README](README.md) is the current entry point; [the pipeline decision](docs/decisions/0001-mixed-language-audio-pipeline.md) and [architecture assessment](docs/architecture/mixed-language-fastapi.md) supersede older stack suggestions. New sessions load context through `CONTEXT-BOOT.md` and wait for direction. Backend building remains paused; future service instructions below are references, not startup actions.

## 1. Select this repo in the new environment

Select the private `Kikiland-ai/kiki-backend` repo and current `main` branch in the new work environment. Use the repo root as the working directory (for example `/workspace/kiki-backend`); verify the published docs, speech module and evidence archive are present. The committed snapshot supplies context; conversation history, API credentials, tool access and native BB8 installation do not automatically transfer.

Runtime baseline:

- Git and Python 3.12 for the existing standard-library prototypes and offline checks; no application dependencies need installing to run them.
- Git LFS for the concept-canvas narration WAVs under `artifacts/cam-review/`. Run `git lfs install` once before cloning, or `git lfs pull` in an existing clone; without it those files are small pointer texts and `scripts/verify-cam-review.py` fails.
- FastAPI with durable job coordination and bounded stage workers is the selected future backend direction. Database, queue/actor framework, object storage and package-management/lockfile choices remain open; do not scaffold them during context loading.
- Node.js 22 is needed only for the imported JavaScript ledger validator. npm and Java 21 are conditional tooling if the optional Firebase emulator reference below is selected later.
- FFmpeg is used for WAV-to-MP3 conversion and may be used for future GIF/video derivatives. Browser rendering and alignment need separately chosen/installed dependencies; they are not established by this checkout.

Check versions and source integrity before implementation:

```sh
python --version
python -B scripts/verify-context.py
python -B bb8/adapters/reference/bb8.py validate
python -B bb8/adapters/discovery/sync.py --check
```

Offline execution, when requested: `python -B scripts/generate-mixed-script.py --mode fixture`; tests: `python -B -m unittest discover -s tests -v` and `python -B -m unittest discover -s bb8/tests -v`. Optional imported-ledger check with Node.js 22: `node context/design-thinking/data-model/validate.js context/design-thinking/data-model/ledgers`.

BB8 repo wrappers support compatible Codex/Claude clients. Hosted ChatGPT `@bb8` availability is separate; see `bb8/docs/CHATGPT-INSTALL.md`. Use reference mode if native registration is unavailable.

## 2. Configure local services and real providers separately

The starter includes `.env.example`, optional emulator configuration and deny-client-access rules. Its application/emulator variables are proposals, not an implemented configuration loader. Set Gemini credentials through runtime secrets/process variables; the existing CLI reads `GEMINI_API_KEY` and optionally `GEMINI_TEXT_MODEL` from the process environment and does **not** automatically load `.env`.

The text CLI explicitly selects `--mode fixture` or `--mode gemini`; fixtures are labelled synthetic and do not establish provider quality. The separate speech adapter has completed real Gemini trials, preserved in the [evidence archive](prototypes/mixed_script/evidence/2026-10-13/README.md). The historical `MODEL_MODE`, `SPEECH_MODE` and `LAB_OBSERVER_MODE` environment proposals do not wire these modules together. There is no real lab observer.

The Firebase emulator setup below is optional, conditional on a later datastore choice. Its project is `demo-kiki-backend`, distinct from a real development project. Use server-side ownership checks; client writes are denied by the supplied datastore rules.

After adding/locking `firebase-tools` as a development dependency:

```sh
npx firebase emulators:start --project demo-kiki-backend --only auth,firestore,storage
```

Emulator ports are Auth 9099, Firestore 8080, Storage 9199, and UI 4000. A FastAPI development port/start command has not been configured. Use the environment's supported port forwarding when a service is implemented; container networking may require adjusted hostnames/bindings rather than assuming the host's loopback works inside another container.

For authorized live trials, use the selected development project's Gemini Developer API key through environment secrets. The current text and Gemini TTS adapters use `GEMINI_API_KEY`; they do not require a Google Cloud service-account file. Google Cloud application-default credentials/workload identity are separate modes for any later connector that actually requires them. Do not put keys into the context bundle or print/export their values. Verify the selected runtime's host access, project quota and actual model generation access before calling it. Odia–English speech has been generated in the recorded trial; native quality and reliable alignment remain pending. See the prototype guide before overriding its unverified default model.

In managed environments, allow network access through the supported environment configuration for:

- Repository/package access: `github.com`, `registry.npmjs.org`, and installation/download hosts required by selected tools.
- Emulator downloads: `storage.googleapis.com`.
- Gemini Developer API if chosen: `generativelanguage.googleapis.com`.
- Google Cloud services if chosen: `firestore.googleapis.com`, `storage.googleapis.com`, `identitytoolkit.googleapis.com`, `securetoken.googleapis.com`, and the configured identity/token endpoints.
- Cloud TTS if chosen: `texttospeech.googleapis.com`; alignment/render providers need their own explicit access.

These are required destinations for the selected adapters, not evidence of access or a promise that all services are configured. Keep proxy/CA settings intact. For containers, apply the cloud-runtime skill's proxy/CA instructions before building them. The GitHub identity must have access to the new repo; organization-wide BB8 bootstrap has not been verified as activated and is unnecessary when importing this starter.

## 3. Preserve context as implementation diverges

- `context/design-thinking/` is the pinned upstream source. `context/README.md` establishes authority and reading order.
- `contracts/` is the reserved location for future reconciled implementation schemas and does not exist yet; do not edit copied source types to pretend they reflect an implemented runtime.
- `docs/decisions/` records consequential backend choices and deviations, linked to source sections.
- `docs/plans/active.md` records completed work, actual checks, blockers, fixture/live status, and the next exact action.
- Read the relevant component/source contracts for each feature; presence in the bundle does not mean every file is already loaded by the agent.
- An upstream refresh is an explicit source comparison/migration. Do not track a floating remote document as if the backend baseline changed automatically.

## 4. First session prompt

Paste this into the fresh backend session:

> Use BB8 in this repository in context-loading mode only. Read AGENTS.md and follow CONTEXT-BOOT.md. Load the core sources in its reading order and verify the pinned baseline if tools are available. Report what you actually read, your understanding, and any missing or conflicting context. Do not begin implementation, install dependencies, run services, or modify files. Then wait for my thoughts on how to move forward.

Context boot is complete when the agent reports the actual sources loaded and waits. It does not require an API, dependencies, credentials, or running services. If the repo is not attached/readable, the agent must report that rather than claim this context was loaded.

## 5. Later implementation reference — only after the user requests building

The earlier TypeScript/Fastify/Firebase recommendation is superseded by the user's FastAPI decision. The planned first backend slice reuses existing text/speech code through a bounded job endpoint, with two independent Odia/English proficiency settings, durable checkpoints and owner-scoped artifacts. Concrete runtime schemas, datastore, queue/actor framework and timing/renderer libraries remain decisions to make. Current graphics/live-screen work is a separate [design handoff](docs/handoffs/graphics-and-annotation.md), not an instruction to build the backend.

Live speech has been generated; formal scientific/native-Odia/pronunciation review and sentence alignment remain pending. Graphics rendering and real Simulink observation/overlay access are unimplemented. WPM is a future measured soft-target proposal; the current speech style is fixed.

Once implementation is requested, the relevant setup acceptance criteria are:

- Source integrity and BB8 checks pass; the imported source matches its manifest.
- Backend dependencies/runtime versions and reproducible install are declared with the selected package manager.
- One bounded FastAPI job API starts, validates source/profile input and exposes stage readiness.
- The selected job store/queue preserves validated stage checkpoints across retries/restarts and enforces learner ownership at the API/asset boundary.
- No real provider/tool is reported working until a documented smoke trial succeeds.
- The active plan explicitly records unresolved TTS quality/timing, scientific graphics review, and real Simulink observation/overlay capability.
- Future agents can continue from the active plan and files without this chat.
