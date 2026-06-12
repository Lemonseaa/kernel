# Reference Projects

## Purpose

This file records projects CheckpointAI should learn from.

It separates two categories:

```text
strategic references = learn product/architecture ideas, do not copy code
replacement wheels   = use mature external tools instead of rebuilding plumbing
```

This keeps CheckpointAI focused:

```text
CheckpointAI = external workflow evidence harness
```

It should not become another Dify, Nexent, Archon, Temporal, Prefect, or LiteLLM.

---

## Strategic References

These projects shape how CheckpointAI thinks, but they are not direct code dependencies.

### Archon

Position:

```text
AI coding harness / workflow standardization layer
```

What:

Archon shows how AI work can be made repeatable by putting agents inside a workflow harness.
It treats workflow structure, verification, approvals, and execution context as first-class
engineering objects.

When to learn from it:

```text
When CheckpointAI needs stronger workflow contract discipline:
- clear run stages
- deterministic verification steps
- approval gates
- reusable workflow skeletons
```

How it maps to CheckpointAI:

```text
Archon executes structured AI workflows.
CheckpointAI observes external workflows and judges whether changes improved them.
```

Not:

```text
Do not clone Archon as an AI coding workflow platform.
Do not make CheckpointAI a YAML workflow runner just because Archon uses that shape.
```

### ARIS

Position:

```text
research loop methodology with adversarial review and audit trail
```

What:

ARIS is the most important reference for CheckpointAI's evidence direction. It shows that
long-running AI systems need independent review, persistent artifacts, explicit claims, and
auditable reasoning instead of vague "self-improvement".

When to learn from it:

```text
When CheckpointAI needs stronger evidence review:
- baseline/candidate comparison
- claim checking
- adversarial review
- handoff artifacts
- confidence boundaries
```

How it maps to CheckpointAI:

```text
ARIS reviews research experiments.
CheckpointAI reviews external workflow changes.
```

Not:

```text
Do not turn CheckpointAI into a paper-writing or academic research tool.
Borrow the audit loop, not the domain.
```

### learn-harness-engineering

Position:

```text
harness engineering curriculum and design vocabulary
```

What:

The value is conceptual: a capable model is not enough; the harness around it determines
whether work becomes reproducible, verifiable, and safe.

When to learn from it:

```text
When deciding what belongs in CheckpointAI and what should remain outside:
- instructions
- state
- verification
- scope
- lifecycle
```

How it maps to CheckpointAI:

```text
It explains the discipline.
CheckpointAI implements a narrow part of that discipline: evidence for external workflow changes.
```

Not:

```text
Do not copy course projects into the product.
Use it as a filter for architecture decisions.
```

### Nexent

Position:

```text
no-code / natural-language agent platform
```

What:

Nexent is a platform reference. It shows a possible end-user experience for generating agents,
connecting tools, managing memory, and versioning agent behavior.

When to learn from it:

```text
When designing UI/product experience:
- natural-language configuration
- agent versioning
- tool ecosystem integration
- personal knowledge boundaries
```

How it maps to CheckpointAI:

```text
Nexent helps users create and run agents.
CheckpointAI helps users inspect and improve workflows that may come from Nexent-like systems.
```

Not:

```text
Do not compete with Nexent as a zero-code agent platform.
Do not build a full agent marketplace.
```

---

## Replacement Wheels

These projects are candidates for replacing old CheckpointAI plumbing.

Detailed module mapping lives in:

```text
docs/borrowed_wheels/legacy_replacement_matrix.md
```

### APScheduler

Replaces:

```text
internal scheduler / interval jobs / cron-like logic
```

CheckpointAI rule:

```text
Use APScheduler or cron when recurring local jobs are needed.
Do not expand checkpoint_ai/scheduler as a platform.
```

### Temporal

Replaces:

```text
durable workflow execution / retries / HA failover
```

CheckpointAI rule:

```text
Use Temporal only when durable workflow orchestration is truly needed.
Do not build HA orchestration inside CheckpointAI.
```

### Prefect

Replaces:

```text
data/workflow orchestration for Python pipelines
```

CheckpointAI rule:

```text
Reference or integrate with Prefect for pipeline execution.
CheckpointAI should stay in the evidence and decision layer.
```

### LiteLLM

Replaces:

```text
full LLM provider platform / broad model routing / provider proxy
```

CheckpointAI rule:

```text
Do not build a model console.
Use a thin adapter or LiteLLM-compatible layer when broad provider coverage is needed.
```

### MCP Servers

Replaces:

```text
custom plugin marketplace / generic tool ecosystem
```

CheckpointAI rule:

```text
Use guarded MCP/tool connectors.
External tools are not trusted by default.
Sensitive side effects still require policy and human boundaries.
```

---

## Decision Rule

Before adding a module, ask:

```text
Is this evidence, comparison, visualization, decision, or rollback?
```

If yes:

```text
Build it in CheckpointAI.
```

If no:

```text
Find an external wheel, adapter, or reference pattern.
```
