# 0019 — Draft trader and streamer content bundles

20 November 2026. User requested a new branch based on PR #13 to create content for the two
knowledge-worker personas. Branch: `feat/trader-streamer-content`, parent `940065c`.

## Sources and scope

The named design-review chat was not available through this session's tools. The implementation
uses the published Design-Thinking knowledge-worker direction and persona playbooks at
`45180af3f589bfdb11711766a4f8fbbc339a8ce9`. Twelve relevant sources are preserved unmodified
under `content/knowledge-workers/sources/design/`, with hashes and original paths in a manifest.
The older pinned `context/design-thinking/` baseline is not refreshed.

The playbooks explicitly propose four concepts per module. Implement those two modules in
the PR's packet format rather than inventing a wider course. The trader covers IV, time,
entry risk and process records. The streamer covers hooks, participation signals, count ratios
and a one-change review plan. Each has Learn content, authored Do tasks and Reflect links.

## Decisions

- Packets and plans are the authored sources. A standard-library assembler reuses the PR
  checker and writes deterministic `kiki-pack/v0` draft exports plus authoring sidecars.
- English lesson sources are available. Hindi and Hinglish glossary support and unchanged
  inherited tutor lines are machine drafts. No target lesson rendition or audio is invented.
- Cases, people and organisation rules remain illustrative. Distinguish org heuristics from
  general facts, entry risk from realised loss, concurrent counts from individuals, and
  correlation from causal evidence.
- Adapt inherited tutor graphs to canonical `nextSteps`, resolve all content links, remove
  scripted scorecards, avoid assuming what a learner has demonstrated, and qualify causal
  claims. Changed lines remain English-only pending translation and native review.
- Practice predictions are content, not observed practice evidence. Keep all four dimension
  keys; display Expression and Practice without renaming `english` or `lab`.
- Add bundle-level protection for the three checker gaps found in review: duplicate placard
  ids, empty widget expectations and missing objective references. Do not change the shared
  skill checker as part of this content implementation.

## Consequences

This is an offline content layer, not publication or a new runtime. Proposed static DomainPack
exports do not supersede [ADR 0011](0011-generated-content-reaches-kiki-web-through-the-database.md)
for generation/storage delivery. Choose the relevant ingestion path when integrating the new
knowledge-worker route. Lesson reads must not trigger generation.

Domain review, native review, translated lesson renditions, actual speech timing, renderer
acceptance and application wiring remain distinct work. A full frozen DomainPack schema mirror
does not yet exist here, so no runtime compatibility acceptance is claimed.

Verification and exact continuation: [content plan](../plans/trader-streamer-content.md).
