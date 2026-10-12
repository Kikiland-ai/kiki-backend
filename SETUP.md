# Start backend work without losing product context

This is a context/runtime starter, not a running API. It carries the source documents and BB8 into `Kikiland-ai/kiki-backend`. The first session must load context through `CONTEXT-BOOT.md` and wait for the user's thoughts. The runtime/service instructions below are reference material for later authorized implementation, not startup actions.

## 1. Select this repo in the new environment

After importing/committing the starter, select the private `Kikiland-ai/kiki-backend` repo and its `main` branch in the new work environment. Use the repo root as the working directory (for example `/workspace/kiki-backend`). Start a fresh session on that environment. The committed snapshot supplies context; conversation history, API credentials, tool access, and native BB8 installation do not automatically transfer.

Runtime baseline:

- Node.js 22, npm, Git, Python 3.12, and Java 21 for the Firestore emulator.
- Commit a lockfile when scaffolding dependencies; subsequent setups use `npm ci`.
- Recommended backend: TypeScript, Fastify, Zod runtime schemas, Firebase Admin SDK, and Vitest. Add the selected renderer/alignment libraries after the small media trials establish the choice.
- Add FFmpeg when producing GIF/video derivatives from rendered frames. A browser renderer needs its browser/system dependencies installed explicitly; Node alone does not establish those capabilities.

Check versions and source integrity before implementation:

```sh
node --version
npm --version
python --version
java -version
python scripts/verify-context.py
python bb8/adapters/reference/bb8.py validate
python bb8/adapters/discovery/sync.py --check
node context/design-thinking/data-model/validate.js context/design-thinking/data-model/ledgers
```

BB8 repo wrappers support compatible Codex/Claude clients. Hosted ChatGPT `@bb8` availability is separate; see `bb8/docs/CHATGPT-INSTALL.md`. Use reference mode if native registration is unavailable.

## 2. Configure local services and real providers separately

The starter includes `.env.example`, emulator configuration, and deny-client-access rules. Copy `.env.example` to an ignored local `.env` or set equivalent runtime variables through environment settings. The first backend implementation must validate/load this configuration; no starter script yet consumes the application variables.

The initial modes are fixtures for model, speech, and tool observations. They must be labelled fixtures and may not count as real speech/tool validation. The emulator project is `demo-kiki-backend`, distinct from a real development project. Use server-side ownership checks; client writes are denied by the supplied datastore rules.

After adding/locking `firebase-tools` as a development dependency:

```sh
npx firebase emulators:start --project demo-kiki-backend --only auth,firestore,storage
```

Emulator ports are Auth 9099, Firestore 8080, Storage 9199, and UI 4000. The API's suggested development port is 3000. Use the environment's supported port forwarding for access; container networking may require adjusted hostnames/bindings rather than assuming the host's loopback works inside another container.

For real-provider trials, create/select a separate development GCP project and configure the chosen Gemini/speech API credentials using environment secrets or supported workload identity. Do not put keys into the context bundle. API-key access and Google Cloud application-default credentials are different modes; the adapters must declare which they need. Use the configured identity normally, without printing or exporting credential values. Billing/quotas and actual Odia capability still need verification; this starter does not configure them.

In managed environments, allow network access through the supported environment configuration for:

- Repository/package access: `github.com`, `registry.npmjs.org`, and installation/download hosts required by selected tools.
- Emulator downloads: `storage.googleapis.com`.
- Gemini Developer API if chosen: `generativelanguage.googleapis.com`.
- Google Cloud services if chosen: `firestore.googleapis.com`, `storage.googleapis.com`, `identitytoolkit.googleapis.com`, `securetoken.googleapis.com`, and the configured identity/token endpoints.
- Cloud TTS if chosen: `texttospeech.googleapis.com`; alignment/render providers need their own explicit access.

These are required destinations for the selected adapters, not evidence of access or a promise that all services are configured. Keep proxy/CA settings intact. For containers, apply the cloud-runtime skill's proxy/CA instructions before building them. The GitHub identity must have access to the new repo; organization-wide BB8 bootstrap has not been verified as activated and is unnecessary when importing this starter.

## 3. Preserve context as implementation diverges

- `context/design-thinking/` is the pinned upstream source. `context/README.md` establishes authority and reading order.
- `contracts/` contains reconciled implementation schemas; do not edit the copied originals to pretend they already reflect the new runtime.
- `docs/decisions/` records consequential backend choices and deviations, linked to source sections.
- `docs/plans/active.md` records completed work, actual checks, blockers, fixture/live status, and the next exact action.
- Read the relevant component/source contracts for each feature; presence in the bundle does not mean every file is already loaded by the agent.
- An upstream refresh is an explicit source comparison/migration. Do not track a floating remote document as if the backend baseline changed automatically.

## 4. First session prompt

Paste this into the fresh backend session:

> Use BB8 in this repository in context-loading mode only. Read AGENTS.md and follow CONTEXT-BOOT.md. Load the core sources in its reading order and verify the pinned baseline if tools are available. Report what you actually read, your understanding, and any missing or conflicting context. Do not begin implementation, install dependencies, run services, or modify files. Then wait for my thoughts on how to move forward.

Context boot is complete when the agent reports the actual sources loaded and waits. It does not require an API, dependencies, credentials, or running services. If the repo is not attached/readable, the agent must report that rather than claim this context was loaded.

## 5. Later implementation reference — only after the user requests building

The earlier proposal suggested starting with a runtime-validated TypeScript API, reconciled lesson/speech/scene/annotation contracts, emulator configuration, a two-concept fixture pack, and a versioned lesson-package endpoint. Keep this as a possible slice, not a committed sequence. Discuss the user's intended direction first. Subsequent live speech/graphics and Simulink trials remain pending.

Once implementation is requested, the relevant setup acceptance criteria are:

- Source integrity and BB8 checks pass; the imported source matches its manifest.
- Backend install is reproducible from a committed lockfile and declared runtime versions.
- One API starts, serves a fixture lesson package, and rejects invalid input through runtime schemas.
- Emulator integration persists/reloads a versioned record and enforces learner ownership at the API boundary.
- No real provider/tool is reported working until a documented smoke trial succeeds.
- The active plan explicitly records unresolved TTS quality/timing, scientific graphics review, and real Simulink observation/overlay capability.
- Future agents can continue from the active plan and files without this chat.
