# Evidence Workflow Visualization Next 5 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the Evidence Console from JSON inspection to a readable workflow map with node-level evidence and risk context.

**Architecture:** Keep workflow extraction and evidence scoring in the backend. The frontend renders a simple deterministic workflow map from `WorkflowVisualization.nodes` and `WorkflowVisualization.edges`, then lets the human inspect each node's trace, metric coverage, black-box status, cost, and latency. No drag-and-drop builder and no workflow editing.

**Tech Stack:** React, TypeScript, Tailwind, Playwright, existing Evidence API.

---

### Task 1: Split Evidence UI Into Focused Components

**Files:**
- Create: `web/src/features/evidence/WorkflowMap.tsx`
- Create: `web/src/features/evidence/NodeInspector.tsx`
- Create: `web/src/features/evidence/MetricDeltaChart.tsx`
- Modify: `web/src/features/evidence/EvidencePage.tsx`
- Test: `web/tests/e2e/console.spec.ts`

- [ ] Move metric delta bar rendering from `EvidencePage.tsx` into `MetricDeltaChart.tsx`.
- [ ] Move workflow node/edge rendering into `WorkflowMap.tsx`.
- [ ] Move selected-node detail rendering into `NodeInspector.tsx`.
- [ ] Keep `EvidencePage.tsx` as page orchestration only: fetch runs, selected run, selected node, comparison mutation.
- [ ] Verify `npm run lint` and `npm run build`.

### Task 2: Render A Deterministic Workflow Map

**Files:**
- Modify: `web/src/features/evidence/WorkflowMap.tsx`
- Modify: `web/tests/e2e/console.spec.ts`

- [ ] Add e2e assertions for visible node labels: `Load data`, `Strategy agent`, `Risk check`.
- [ ] Add e2e assertion for visible path labels or arrows: `data → agent → risk`.
- [ ] Implement a simple non-draggable map using cards and connecting arrows.
- [ ] Mark node type with badges: `tool`, `agent`, `unknown`.
- [ ] Do not introduce graph libraries yet; use stable HTML so tests and layout remain simple.

### Task 3: Add Node-Level Evidence Inspector

**Files:**
- Modify: `web/src/features/evidence/NodeInspector.tsx`
- Modify: `web/src/features/evidence/EvidencePage.tsx`
- Modify: `web/tests/e2e/console.spec.ts`

- [ ] Add e2e step: click `Strategy agent`.
- [ ] Assert inspector shows node id, type, latency, cost, and whether the node is traced.
- [ ] Show `Black-box node` warning when selected node id is in `black_box_node_ids`.
- [ ] Show `Metric captured` when selected node id is in `metric_node_ids`.
- [ ] Default selected node should be the first node in the selected run path.

### Task 4: Visualize Coverage And Black-Box Risk

**Files:**
- Modify: `web/src/features/evidence/WorkflowMap.tsx`
- Modify: `web/src/features/evidence/EvidencePage.tsx`
- Modify: `web/tests/e2e/console.spec.ts`
- Modify: `docs/core_innovation/impact_console.md`

- [ ] Add e2e fixture with one black-box node.
- [ ] Assert black-box node has visible warning text.
- [ ] Render traced nodes, metric nodes, black-box nodes, and error nodes with distinct status labels.
- [ ] Add a small coverage legend: `Traced`, `Metric`, `Black box`, `Error`.
- [ ] Document that visualization is an observability surface, not a workflow builder.

### Task 5: Add Report-To-Action Summary

**Files:**
- Modify: `web/src/features/evidence/EvidencePage.tsx`
- Modify: `web/tests/e2e/console.spec.ts`
- Modify: `docs/core_innovation/impact_console.md`

- [ ] Add a compact `What to do next` panel beside the workflow map.
- [ ] If recommendation contains `approve`, show `Review candidate approval`.
- [ ] If black-box nodes exist, show `Add trace coverage before trusting this workflow`.
- [ ] If metric coverage is below `0.8`, show `Improve metric capture before optimization`.
- [ ] Add e2e assertions for these action summaries.

### Verification

Run from `/Users/lemonsea/Desktop/mas/loop-harness`:

```bash
cd web && npm run lint
cd web && npm run build
cd web && npm run e2e
python -m unittest discover -s tests -q
python -m ruff check loop_harness tests scripts
python -m mypy loop_harness --show-error-codes --no-incremental
python scripts/ops/final_acceptance.py
```

Expected result:

```text
frontend lint/build/e2e pass
256 backend tests pass
ruff pass
mypy pass
acceptance_summary status=passed
```
