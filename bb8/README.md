# BB8 cloud plugin package

This is a portable, skills-only BB8 plugin package for Codex and compatible
agent-plugin hosts.

It contains:

- the 22-skill BB8 suite (the original 21 plus the user-supplied prompt-design-engineering skill);
- the BB8 harness files required by those skills;
- a portable root `plugin.json` manifest;
- a Codex-compatible `.codex-plugin/plugin.json` manifest;
- the deterministic local Organise helper script and its generic references;
- a receiving-session setup runbook.

It intentionally does **not** contain project files, a knowledge vault, chats,
memories, account configuration, credentials, tokens, caches, logs, or a
preselected knowledge-root path.

Use `SESSION-SETUP-RUNBOOK.md` as the instruction source for the receiving
session. For an OpenAI-hosted sandbox, upload the ZIP whose top level is this
`bb8` folder. For a self-hosted sandbox, register this folder itself as a
capability directory.

## Skill inventory

1. `bb8`
2. `data-analysis`
3. `deep-research`
4. `design-critique`
5. `engineering`
6. `engineering-architecture`
7. `engineering-debugging`
8. `engineering-implementation`
9. `engineering-review`
10. `engineering-security`
11. `engineering-testing`
12. `experience-design`
13. `experiment-design`
14. `minto-communication`
15. `organise`
16. `problem-solving`
17. `product-design`
18. `product-discovery`
19. `product-strategy`
20. `strategic-storytelling`
21. `transcript-insights-tofu`
22. `prompt-design-engineering`

The 0.2.2 extension preserves the supplied skill text byte for byte. Existing canonical skill texts remain unchanged. Native hosted activation is a separate acceptance step.
