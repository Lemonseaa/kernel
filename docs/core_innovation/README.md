# Core Innovation

This folder contains the parts CheckpointAI should own.

CheckpointAI's core innovation is not another Agent runtime. It is the evidence layer around external workflows:

```text
External workflow run
  -> workflow contract
  -> workflow visualization
  -> trace / metric coverage
  -> baseline vs candidate comparison
  -> evidence review
  -> human decision / rollback
```

## What Belongs Here

- Evidence Harness design.
- Workflow visualization and black-box diagnosis.
- Impact Console for human evidence review.
- Metric schema and evidence review.
- Human methodology and preference boundaries.
- Approval, rollback, and decision evidence.

## What Does Not Belong Here

- External project summaries.
- Replacement wheels.
- Business-line-specific reports.
- Historical version acceptance notes.

## Current Files

- [metrics_reference.md](metrics_reference.md): metric direction, category, and comparison reference.
- [impact_console.md](impact_console.md): UI scope and Evidence API boundaries.
- [user_preference.md](user_preference.md): human-owned methodology, preference, and Hermes draft flow.
