---
name: prompt-design-engineering
description: Design, debug, review, and optimize production LLM prompts as testable contracts. Use for system prompts, agent personas, routers, classifiers, structured extractors, generators, summarizers, and tool descriptions.
---

# Prompt Design and Engineering

Portable adaptation of LongGait legacy skills `w004_prompt_architecture` and `w208_prompt_engineering`.

## Core principle

A prompt is a contract, not a suggestion.

- Explicit beats implicit.
- Constraints beat wishes.
- Examples beat abstract descriptions.
- Verifiable requirements beat subjective language.
- If compliance cannot be checked, it cannot be enforced reliably.

## Operating modes

Choose the mode that matches the request:

- **Design:** Create a new prompt using the six-layer architecture.
- **Debug:** Identify the failure class before changing the prompt.
- **Optimize:** Improve measured performance one change at a time.
- **Review:** Audit a prompt against the production checklist.
- **Coherence:** Check vocabulary, schemas, routing, and versions across a multi-prompt system.

## Six-layer prompt architecture

Include only the layers the task needs, but audit all six.

### 1. Identity — who

Define:

- the role;
- relevant domain expertise;
- the primary job;
- important behavioral distinctions;
- scope and authority;
- an explicit **“you are not”** clause for likely drift modes.

### 2. Context — what

Provide:

- the input type and provenance;
- necessary domain facts and canonical vocabulary;
- trust-boundary or data-sensitivity constraints;
- assumptions the model may use;
- assumptions the model must not make.

Keep deterministic facts, enums, and schemas in canonical code or data sources where possible. Do not ask the model to recreate them from memory.

### 3. Task — how

State:

- the single primary objective;
- the exact output shape;
- required and optional fields;
- field-level constraints;
- success and failure behavior;
- how to handle empty, missing, or ambiguous input.

For structured output, use the provider’s strict schema feature when available and repeat critical field semantics in the prompt.

### 4. Guardrails — boundaries

Specify:

- what the model may use;
- what it must not infer or invent;
- prohibited actions or content;
- escalation, refusal, or abstention rules;
- preservation of uncertainty;
- safe failure behavior.

Positive targets work better than negative-only rules. Prefer “Only include claims supported by the supplied source” over “Do not hallucinate.”

Prompt text is not a substitute for architectural safety, authorization checks, redaction, output validation, or access control.

### 5. Validation — check

Before output, require concrete checks such as:

- every claim traces to supplied evidence;
- every required field exists;
- enum values are valid;
- output parses against the schema;
- quotations or source spans match the input;
- uncertainty markers remain intact;
- no forbidden inference was introduced.

Validation must reference specific fields and rules, not vague instructions such as “be accurate.”

### 6. Examples — show

Use two or three hard examples when needed:

- one correct example;
- one negative example showing the most likely failure;
- optionally one edge case.

Explain why the negative example fails. Avoid easy or numerous examples that add cost, bias surface patterns, or crowd out the live input.

## Production forcing functions

Every production prompt should pass these gates:

1. **Verifiability:** Every important constraint can be tested.
2. **One change:** Change one meaningful prompt variable per iteration.
3. **Eval first:** Do not optimize without a representative evaluation set.
4. **Grounding:** Claims trace to source evidence; unsupported claims are omitted.
5. **Schema:** Structured output has a strict schema plus valid and invalid examples.
6. **Data boundary:** Sensitive data stays within the authorized trust boundary.
7. **Eval coupling:** The prompt and its rubric evolve together.
8. **Versioning:** Every production prompt has a version and a rollback path.

Thresholds such as evaluation-set size, temperature, or shadow duration are context-dependent. Choose them from task risk, traffic, model behavior, and evidence rather than treating legacy defaults as universal.

## Reusable prompt template

```markdown
# Identity
You are [specific role] with expertise in [domain].
Your job is to [single primary objective].
You are meticulous about [important distinctions].
You are not [likely drift modes].

# Context
You will receive [input type and provenance].
You may rely on [authorized context].
Treat [data classes] according to [trust-boundary rule].
Do not assume [forbidden assumptions].

# Task
Produce [output type] that [success condition].

Required procedure:
1. [Step]
2. [Step]
3. [Step]

Output must conform to:
[schema or exact format]

Field rules:
- [field]: [type, allowed values, semantics]
- [field]: [type, allowed values, semantics]

For missing or ambiguous information: [null, omit, abstain, ask, or error rule].

# Guardrails
- Use only [authorized evidence].
- Do not invent [task-specific prohibited details].
- Preserve uncertainty words such as [examples].
- If [boundary condition], [refuse/escalate/abstain].

# Validation
Before answering, verify:
1. [machine-checkable criterion]
2. [machine-checkable criterion]
3. [machine-checkable criterion]

# Examples
## Correct hard case
Input: ...
Output: ...
Why: ...

## Incorrect common failure
Input: ...
Bad output: ...
Why it fails: ...
Correct output: ...
```

## Task-specific additions

### Structured extraction

- Require evidence for every finding: quotation, source ID, or validated source span.
- Preserve explicit negative findings when they matter.
- Define empty output as valid and require a reason when useful.
- Never infer identifiers, codes, quantities, dates, or units absent from the source.

### Classification and routing

- Define an exhaustive, mutually exclusive enum where possible.
- Give boundary rules for adjacent classes.
- Include examples of common misclassification.
- Define abstention and critical-class behavior.
- Ensure every router class has a real downstream handler.

### Generation

- Define audience, reading level, tone, and length.
- State content and authority boundaries.
- Define refusal or escalation behavior for unsafe requests.
- Keep style constraints subordinate to factual and safety constraints.

### Summarization

- Set length and coverage rules.
- Use an inclusion allow-list as well as exclusions.
- Preserve uncertainty and attribution.
- Forbid embellishment and unsupported causal claims.

### Tool descriptions

Treat every tool description as a prompt. Include:

- one-sentence purpose;
- argument schema and required fields;
- when to call;
- when not to call;
- expected return shape;
- relevant cost, latency, side-effect, or authorization notes.

## Debugging decision tree

Diagnose before editing.

- **Wrong format or parse errors:** Add a strict schema, field rules, valid/invalid examples, and explicit “no preamble or code fences” instructions. Validate in code.
- **Invented details:** Add evidence requirements, task-specific grounding prohibitions, abstention behavior, and negative examples.
- **Wrong category:** Add exhaustive definitions, adjacent-class disambiguation rules, and boundary examples.
- **Missing required information:** Mark fields required, define empty-input behavior, and add field-specific validation.
- **Inconsistent outputs:** Reduce sampling variance if appropriate, add hard edge cases, remove conflicting instructions, and check context placement.
- **Sensitive-data leakage:** Stop treating it as a prompt issue. Fix redaction, authorization, and data flow before the model call.
- **Unsafe or unauthorized action:** Fix system guardrails and permission checks; do not rely on prompt wording alone.
- **Still failing:** Revisit the rubric. If qualified evaluators disagree on correctness, clarify the target before further tuning.

## Optimization ladder

Climb only when measured results justify the complexity:

1. **Zero-shot:** Clear role, task, and output.
2. **Manual engineering:** Add schema, grounding, validation, role boundaries, and taxonomy rules one at a time.
3. **Few-shot selection:** Add a small number of relevant hard examples.
4. **Automated prompt search:** Use only with a stable metric, training set, and untouched holdout set.
5. **Programmatic optimization:** Use for complex, repeatable pipelines where compilation and reproducibility justify the machinery.

Workflow:

1. Establish a baseline on representative cases.
2. Group failures by class and find the largest class.
3. Make one targeted change.
4. Re-run the same evaluation and check other classes for regressions.
5. Validate on a held-out set.
6. Version, stage or shadow where appropriate, deploy, and monitor.

## Multi-prompt coherence

For routers, agents, tools, and downstream specialists:

- keep shared enums and vocabulary in one canonical source;
- ensure router outputs match downstream capabilities;
- make system prompts accurately describe available tools;
- test schema compatibility between stages;
- update and evaluate coupled prompt versions together;
- apply the same data-classification assumptions across the chain.

## Anti-patterns

- vague instructions such as “be accurate”;
- implicit formats such as “use the standard structure”;
- negative-only rules;
- examples that cover only easy cases;
- large prompt rewrites with no attribution of effects;
- optimization without an evaluation set;
- kitchen-sink prompts with multiple unrelated jobs;
- prompt golf that sacrifices clarity for brevity;
- using prompts as a substitute for security or safety architecture;
- unversioned production prompts;
- repeatedly tuning on the same evaluation set until it becomes training data.

## Review checklist

### Structure

- [ ] Identity names the role, expertise, authority, and “not” boundaries.
- [ ] Context defines input, provenance, assumptions, and data boundary.
- [ ] Task has one objective, exact output, field rules, and empty/error behavior.
- [ ] Guardrails define grounding, prohibitions, uncertainty, and escalation.
- [ ] Validation uses concrete, field-specific checks.
- [ ] Examples cover hard and negative cases where useful.

### Quality and safety

- [ ] Every important constraint is testable.
- [ ] Every factual output can be traced to authorized evidence.
- [ ] Deterministic validation occurs in code where possible.
- [ ] Data redaction and authorization happen outside the prompt.
- [ ] Safety controls do not depend on prompt obedience alone.

### Evaluation and operations

- [ ] A baseline and representative failure cases exist.
- [ ] Changes are isolated and measured.
- [ ] A held-out set checks overfitting.
- [ ] Cost, latency, and failure behavior are measured.
- [ ] The prompt is versioned and rollback is defined.
- [ ] Production monitoring uses the same outcome definitions as evaluation.

## Output behavior when this skill is invoked

- In **design** mode, return the completed six-layer prompt and note any unresolved assumptions.
- In **debug** mode, name the failure class, cite the offending prompt clause or omission, and propose the smallest measurable change.
- In **optimize** mode, provide the baseline, failure taxonomy, one-change experiment, metric, and stopping rule.
- In **review** mode, report concrete findings ordered by risk, then provide a corrected prompt only if requested.
- In **coherence** mode, map producer outputs to consumer inputs and flag vocabulary, schema, safety, or version drift.

## Lineage

- LongGait legacy `meta/w004_prompt_architecture.md`
- LongGait legacy `ai-core/w208_prompt_engineering.md`
- Snapshot date recorded by the library: 2026-09-24

The reusable mechanism is preserved; repository-specific paths, vendor assumptions, domain-sensitive examples, and hard-coded operational thresholds were removed or made contextual.
