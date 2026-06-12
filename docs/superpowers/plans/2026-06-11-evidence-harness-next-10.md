# Evidence Harness Next 10 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn CheckpointAI's Evidence Harness from a working console into a realistic external-workflow optimization loop.

**Architecture:** The core path is external workflow ingestion → visualization → evidence quality → baseline comparison → proposal → shadow/replay → approval/action → learning record. Reuse existing backend Evidence API, adapter contracts, approval inbox, and UI shell. Do not rebuild Dify, workflow engines, model consoles, or plugin marketplaces.

**Tech Stack:** Python, FastAPI, SQLite, React, TypeScript, Tailwind, Playwright, existing CheckpointAI modules.

---

## Boundary

This plan is not about adding more Agent OS features.

It focuses on the product's core innovation:

```text
External workflow comes in
CheckpointAI makes it observable
CheckpointAI compares changes against baseline
CheckpointAI tells the human what improved, what worsened, and what is still unsafe
```

---

### Task 1: Evidence Run Detail API

**Purpose:** The UI needs a single endpoint that returns one run with visualization, report, comparison context, and action summary.

**Files:**
- Modify: `checkpoint_ai/api.py`
- Modify: `checkpoint_ai/evidence/store.py`
- Test: `tests/support/test_v58_web_api.py`

**Implementation steps:**

- [ ] Add `GET /api/evidence/runs/{run_id}`.
- [ ] Return the same shape as `StoredEvidenceRun`.
- [ ] Return API error envelope with `404` when run is missing.
- [ ] Add test that ingests a run, fetches it by id, and verifies `run`, `visualization`, and `report` exist.
- [ ] Add test that missing run returns structured error envelope.

**Verification:**

```bash
python -m unittest tests.support.test_v58_web_api -v
```

---

### Task 2: Evidence Run Detail UI Route

**Purpose:** The list page is getting too dense. A run should have a dedicated detail page.

**Files:**
- Create: `web/src/features/evidence/EvidenceRunDetailPage.tsx`
- Modify: `web/src/app/App.tsx`
- Modify: `web/src/api/client.ts`
- Modify: `web/src/types/api.ts`
- Modify: `web/tests/e2e/console.spec.ts`

**Implementation steps:**

- [ ] Add client function `getEvidenceRun(runId: string)`.
- [ ] Add route `/evidence/runs/:runId`.
- [ ] Add "Open" action from Evidence run list.
- [ ] Detail page reuses `WorkflowMap`, `NodeInspector`, and report summary.
- [ ] E2E asserts clicking a run opens `/evidence/runs/baseline-run-001`.

**Verification:**

```bash
cd web && npm run lint
cd web && npm run build
cd web && npm run e2e
```

---

### Task 3: Evidence Quality Gate

**Purpose:** The system must reject or warn on low-quality evidence before comparison becomes trusted.

**Files:**
- Create: `checkpoint_ai/evidence/quality.py`
- Modify: `checkpoint_ai/evidence/models.py`
- Modify: `checkpoint_ai/evidence/service.py`
- Test: `tests/evidence/test_evidence_quality.py`

**Implementation steps:**

- [ ] Define `EvidenceQualityStatus`: `accepted`, `warning`, `rejected`.
- [ ] Score trace coverage, metric coverage, black-box count, run kind, and sample count.
- [ ] Reject comparison trust when run kind is `synthetic` and sample count is too low.
- [ ] Add quality result into `EvidenceReport.evidence`.
- [ ] Tests cover accepted historical run, warning black-box run, rejected low-sample synthetic run.

**Verification:**

```bash
python -m unittest tests.evidence.test_evidence_quality -v
```

---

### Task 4: UI Evidence Quality Panel

**Purpose:** Humans must see whether evidence is trustworthy before approving a change.

**Files:**
- Create: `web/src/features/evidence/EvidenceQualityPanel.tsx`
- Modify: `web/src/features/evidence/EvidencePage.tsx`
- Modify: `web/src/features/evidence/EvidenceRunDetailPage.tsx`
- Modify: `web/tests/e2e/console.spec.ts`

**Implementation steps:**

- [ ] Render quality status from `report.evidence.quality`.
- [ ] Show reasons: low trace coverage, low metric coverage, black-box nodes, synthetic run, low sample count.
- [ ] Use warning styling, not blocking UI behavior.
- [ ] E2E asserts black-box fixture shows quality warning.

**Verification:**

```bash
cd web && npm run e2e
```

---

### Task 5: Baseline Selection Persistence

**Purpose:** Comparing random runs is not enough. Each workflow needs a current baseline.

**Files:**
- Create: `checkpoint_ai/evidence/baseline_store.py`
- Modify: `checkpoint_ai/evidence/service.py`
- Modify: `checkpoint_ai/api.py`
- Test: `tests/evidence/test_evidence_baseline.py`

**Implementation steps:**

- [ ] Add SQLite table `evidence_baselines`.
- [ ] Store `workflow_id`, `baseline_run_id`, `reason`, `created_at`.
- [ ] Add API `POST /api/evidence/workflows/{workflow_id}/baseline`.
- [ ] Add API `GET /api/evidence/workflows/{workflow_id}/baseline`.
- [ ] Compare endpoint defaults to stored baseline when baseline id is omitted.

**Verification:**

```bash
python -m unittest tests.evidence.test_evidence_baseline -v
```

---

### Task 6: UI Baseline Pinning

**Purpose:** Human should be able to say "this is my baseline" from the console.

**Files:**
- Modify: `web/src/api/client.ts`
- Modify: `web/src/types/api.ts`
- Modify: `web/src/features/evidence/EvidencePage.tsx`
- Modify: `web/src/features/evidence/EvidenceRunDetailPage.tsx`
- Modify: `web/tests/e2e/console.spec.ts`

**Implementation steps:**

- [ ] Add client functions `getEvidenceBaseline` and `setEvidenceBaseline`.
- [ ] Add "Set as baseline" button on run detail.
- [ ] Show active baseline badge in run list.
- [ ] Compare panel defaults baseline selector to pinned baseline.
- [ ] E2E asserts pinning baseline updates the UI.

**Verification:**

```bash
cd web && npm run lint
cd web && npm run build
cd web && npm run e2e
```

---

### Task 7: Proposal From Evidence Comparison

**Purpose:** A comparison that improves metrics should create a human-reviewable proposal, not just a report.

**Files:**
- Modify: `checkpoint_ai/evidence/service.py`
- Modify: `checkpoint_ai/prompt/models.py`
- Modify: `checkpoint_ai/console/approval_inbox.py`
- Modify: `checkpoint_ai/api.py`
- Test: `tests/evidence/test_evidence_to_proposal.py`

**Implementation steps:**

- [ ] Add `EvidenceProposal` or reuse generic `Proposal` with `proposal_type="evidence_candidate"`.
- [ ] Create proposal from comparison only when `recommendation` contains `approve` and quality is not rejected.
- [ ] Include baseline id, candidate id, metric delta, quality status, and reason.
- [ ] Proposal appears in existing approval inbox.
- [ ] Tests verify rejected evidence does not create proposal.

**Verification:**

```bash
python -m unittest tests.evidence.test_evidence_to_proposal -v
```

---

### Task 8: UI Evidence Approval Bridge

**Purpose:** Evidence comparison should naturally lead to Approval Inbox instead of being a dead-end report.

**Files:**
- Modify: `web/src/api/client.ts`
- Modify: `web/src/features/evidence/EvidencePage.tsx`
- Modify: `web/src/features/evidence/EvidenceRunDetailPage.tsx`
- Modify: `web/tests/e2e/console.spec.ts`

**Implementation steps:**

- [ ] Add "Create approval proposal" button after successful comparison.
- [ ] Disable button when quality is rejected.
- [ ] On success, show proposal id and link to `/approvals/:id`.
- [ ] E2E asserts compare → create proposal → approval link appears.

**Verification:**

```bash
cd web && npm run e2e
```

---

### Task 9: Real Data Drill Command

**Purpose:** Before entering the next product phase, we need a repeatable evidence drill that creates enough runs to inspect UI, baseline, quality, and proposal flow.

**Files:**
- Create: `scripts/business_lines/run_evidence_drill.py`
- Modify: `scripts/README.md`
- Test: `tests/business_lines/quant/test_evidence_drill.py`

**Implementation steps:**

- [ ] Generate at least 10 historical-style evidence runs for one workflow.
- [ ] Include at least one black-box run, one rejected low-quality run, one candidate improvement, and one regression.
- [ ] Pin a baseline.
- [ ] Produce at least one comparison and one proposal.
- [ ] Print a human-readable summary.

**Verification:**

```bash
python scripts/business_lines/run_evidence_drill.py
python -m unittest tests.business_lines.quant.test_evidence_drill -v
```

---

### Task 10: Final Acceptance And Risk Review

**Purpose:** This batch touches backend API, UI, persistence, and approval flow. It needs a focused risk review before commit.

**Files:**
- Create: `docs/core_innovation/evidence_harness_risk_review.md`
- Modify: `docs/core_innovation/impact_console.md`
- Modify: `docs/BLUEPRINT.md`

**Implementation steps:**

- [ ] Document what is now proven.
- [ ] Document what is still not proven: live deployment, real trading edge, real content growth, long-term learning.
- [ ] Document rollback path for baseline/proposal mistakes.
- [ ] Run full backend and frontend verification.
- [ ] Write final risk review with remaining blockers.

**Verification:**

```bash
cd web && npm run lint
cd web && npm run build
cd web && npm run e2e
python -m unittest discover -s tests -q
python -m ruff check checkpoint_ai tests scripts
python -m mypy checkpoint_ai --show-error-codes --no-incremental
python scripts/ops/final_acceptance.py
```

Expected result:

```text
frontend lint/build/e2e pass
backend tests pass
ruff pass
mypy pass
acceptance_summary status=passed
```

---

## Execution Order

```text
1. Run detail API
2. Run detail UI
3. Evidence quality backend
4. Evidence quality UI
5. Baseline persistence
6. Baseline UI
7. Proposal bridge backend
8. Proposal bridge UI
9. Real data drill
10. Acceptance + risk review
```

This order is intentional:

```text
observe first
then judge evidence quality
then compare against a pinned baseline
then create approval proposals
then run enough data to expose flaws
```
