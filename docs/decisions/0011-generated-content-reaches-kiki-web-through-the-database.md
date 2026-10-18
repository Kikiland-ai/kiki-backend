# Generated content reaches kiki-web through the database

18 October 2026. User decision, made while mapping the frontend integration after the branch reconciliation.

## Decision

The mixed-language text and audio job API (`/v1/mixed-language-jobs`, `prototypes/mixed_language/`) is a content-generation path. It is invoked from the database side, and what it produces is stored there. kiki-web reads the stored content; neither the browser nor kiki-web's `apps/api` calls the job API.

User statement:

> "the mixed language job api is used for content generation and now that will be used directly to be called from the DB, so explicit connection to that api is not necessary path now."

## Why

- kiki-web's rule is that a lesson read never generates content (`apps/web/CONCEPT_MEDIA.md`). Generation belongs before publication, not in the student's request path.
- It removes a second upstream from kiki-web's API. The only kiki-web → kiki-backend connection stays the lab-execution allowlist ([ADR 0010](0010-kiki-web-api-fronts-lab-execution.md)).

## Consequences

- No kiki-web route, proxy entry or browser client is needed for `/v1/mixed-language-jobs`.
- What generation writes must still match what kiki-web reads: per-placard renditions keyed `en`/`or`, the `kiki-web/narration-provenance/v1` hashes, and kiki-web's review keys. The mapping from kiki-web's language dial (1–5) and self-ratings (1–10) to the job's two 0–10 proficiency scores has to be decided where generation is triggered.
- The storage location of generated assets is part of the media-hosting work, which is tracked separately.
- How the database side triggers jobs (for example a queue, a trigger or a scheduled batch) is not decided here.
