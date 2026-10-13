# Commit identity correction

13 October 2026

The authenticated GitHub connection was verified as `arpanvihan5-sketch`, user id `317357476`. An unrelated image-level Git name/email caused the five original backend commits to be displayed as authored and committed by `adityathenerd`, despite the connected account being Arpan's. The user explicitly requested correction of those commits and the four similarly affected Design-Thinking commits.

Author and committer headers are now `arpanvihan5-sketch <317357476+arpanvihan5-sketch@users.noreply.github.com>`. Original messages, timestamps, and file trees were preserved. New ids replace the original reachable commit history; normal follow-up commits reconcile provenance and enforce future identity checks. Unrelated contributor identities in the source repo remain intact.

The pinned source revision is now `73d16c0d967a5d81dd74f1f28ef0defc48c8a778`, with the same file tree and all 130 source hashes unchanged. BB8 provenance points to its equivalent corrected source revision. STARTER-MANIFEST.json has been refreshed as an identity-corrected handoff baseline; it does not freeze ongoing backend implementation or replace SOURCE.json.

Root agent instructions require the verified Git identity before every authorized commit. Global and per-repo defaults were corrected in this execution environment; a new environment must still follow the repo instructions rather than inherit image defaults. No credential values were read or printed. Context-only startup continues to read and wait, without configuring Git or starting implementation until authorized.

History updates use explicit expected-head leases. Local recovery bundles/maps remain outside the repos, without publishing an old-history branch. GitHub may retain old object links or contribution caches after a rewrite; corrected main history is the authoritative attribution. Existing clones/environments must preserve uncommitted/local-only work and reconcile the rewritten history, preferably by using a fresh checkout. Do not force-reset a dirty checkout or merge the old branch back into main.
