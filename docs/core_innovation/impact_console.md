# Impact Console

Impact Console is the human control surface for the Evidence Harness.

It is not a workflow builder, code editor, file browser, model console, or Agent marketplace.

## Primary Job

The console answers:

```text
What changed?
What evidence exists?
Did the candidate beat the baseline?
Where is the workflow still black-box?
Should the human approve, reject, continue shadow, or roll back?
```

## Primary API

New UI work should start from the Evidence Harness API:

```text
POST /api/evidence/runs
GET  /api/evidence/runs?workflow_id=...
GET  /api/evidence/runs/{run_id}/visualization
GET  /api/evidence/runs/{run_id}/report
POST /api/evidence/compare
```

Older `/api/runs` and scenario adapter routes are compatibility/control-console paths.
They should not become the main workflow visualization path.

## P0 Screens

```text
Dashboard
Evidence run list
Workflow visualization
Baseline vs candidate comparison
Evidence report
Approval inbox
Rollback / backup entry
```

## Baseline Comparison View

The comparison view must show optimization impact visually, not only as JSON.

Minimum evidence:

```text
Baseline run
Candidate run
Recommendation
Human-readable summary
Business metric delta
System metric delta
Data quality metric delta
Evidence quality
Approval proposal entry
```

The UI may render simple bars before introducing a charting library.
The important rule is that the human can see whether the candidate improved,
what got worse, and whether the evidence is clean enough to trust.

## Workflow Visualization View

Workflow visualization is an observability surface.
It shows how an external workflow actually ran; it does not edit the workflow.

Minimum evidence:

```text
Node labels
Execution path
Trace coverage
Metric coverage
Black-box nodes
Error nodes
Node latency
Node cost
Next action summary
Pinned baseline marker
```

The first version should use deterministic HTML cards and arrows.
Graph libraries are optional later, after the evidence contract is stable.

## Approval Bridge

When a candidate beats a pinned baseline and evidence quality is not rejected,
the console may create an approval proposal.

This proposal is still a review artifact:

```text
no external workflow mutation
no live deployment
no automatic publishing
no live trading
```

The proposal must include baseline id, candidate id, metric deltas, and quality status.

## Hard Boundaries

```text
No drag-and-drop workflow builder
No direct code editing
No direct database editing
No plugin marketplace
No full model provider console
No automatic live trading or publishing approval
```
