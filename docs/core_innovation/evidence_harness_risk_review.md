# Evidence Harness Risk Review

## Proven In This Batch

LoopHarness can now:

```text
ingest external workflow runs
return one run detail through the API
visualize workflow nodes and paths in the console
inspect node-level trace, metric, latency, cost, and black-box status
score evidence quality
pin a workflow baseline
compare candidate against baseline
create an approval proposal from an improved trusted comparison
run a repeatable quant-shaped evidence drill
```

## Still Not Proven

LoopHarness has not proven:

```text
real trading alpha
safe live trading deployment
real social media growth
long-term autonomous learning
cross-workflow transfer
robust behavior under large production datasets
```

## Current Safety Boundary

Evidence proposals are review artifacts.
They do not execute live trading, publish content, or mutate an external workflow.

The human still controls:

```text
baseline choice
proposal approval
deployment timing
rollback decision
```

## Main Risks

1. Evidence quality can be gamed by synthetic or small-sample runs.
2. Black-box external workflow nodes can hide the true cause of improvement.
3. A candidate can improve one business metric while worsening operational risk.
4. Baseline mistakes can make a weak candidate look strong.
5. UI summaries can make evidence feel more certain than it is.

## Required Mitigations

```text
show evidence quality beside every recommendation
keep black-box warnings visible
require pinned baseline before trusted comparison
store proposal metadata with baseline/candidate ids
keep approval human-controlled
run real-data drills before each major product phase
```

## Rollback Path

If a baseline or proposal is wrong:

```text
pin a different baseline
reject the evidence proposal
restore from backup if persistence state is corrupted
rerun the evidence drill to recreate validation data
```
