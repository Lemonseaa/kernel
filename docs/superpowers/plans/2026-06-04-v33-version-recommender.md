# V3.3 Version Recommender Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Recommend prompt/strategy versions from stored evidence without generating new proposals or running learning algorithms.

**Architecture:** V3.3 consumes V3.1 `EvidenceEvaluationEngine` and V3.2 scenario metric schemas to rank existing proposals/shadow results. It records recommendation decisions as auditable artifacts with explicit reasons, confidence, and source evidence. This is a conservative Champion/Challenger-style recommender, not Bandit, BO, or automatic prompt rewriting.

**Tech Stack:** Python 3.13, Pydantic, SQLite, unittest, ruff, mypy.

---

## Scope

V3.3 does:

1. Aggregate evidence across `ShadowResult` rows for one scenario.
2. Produce auditable recommendations for existing prompt/strategy proposals.
3. Recommend only when evidence is `improved`, non-synthetic, sample count is sufficient, and guardrails are clean.
4. Store recommendation records with source shadow ids and reasons.
5. Add CLI/report commands so humans can inspect recommendations.

V3.3 does not:

1. Generate new PromptProposal or StrategyProposal.
2. Modify prompt text automatically.
3. Auto-apply recommendations.
4. Implement Contextual Bandit.
5. Implement Bayesian Optimization.
6. Learn cross-scenario patterns.

---

## Why Not Bandit Yet

Bandit requires arms, repeated selection opportunities, stable reward definitions, and enough observations per arm. The current system has proposal/shadow results, but not enough real historical/paper/live evidence to justify online allocation.

So V3.3 is deliberately simpler:

```
existing proposal + shadow result + evidence evaluation
  -> recommendation candidate
  -> rank by confidence/objective_score/sample_count
  -> store recommendation
  -> human decides
```

This gives CheckpointAI a useful recommendation layer without pretending to learn from small or synthetic samples.

---

## File Structure

Create:

- `checkpoint_ai/recommendation/__init__.py`  
  Public exports.

- `checkpoint_ai/recommendation/models.py`  
  `RecommendationDecision`, `RecommendationStatus`, `VersionRecommendation`.

- `checkpoint_ai/recommendation/store.py`  
  SQLite storage for recommendations.

- `checkpoint_ai/recommendation/recommender.py`  
  `VersionRecommender`, evidence aggregation and ranking.

- `tests/test_v33_version_recommender.py`  
  V3.3 tests.

Modify:

- `checkpoint_ai/reporting.py`  
  Add recommendation report.

- `checkpoint_ai/v2_cli.py`  
  Add `recommendation` command group. Keep current CLI name for now; do not rename to v3_cli in this version.

- `docs/BLUEPRINT.md`  
  Update V3.3 scope and prerequisites.

Optional after implementation:

- `scripts/run_v29_quant_data.py`  
  Add a short line showing V3.3 would not recommend synthetic runs.

---

## Data Contract

Recommendation model:

```python
class RecommendationDecision(str, Enum):
    RECOMMEND = "recommend"
    REJECT = "reject"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class RecommendationStatus(str, Enum):
    OPEN = "open"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class VersionRecommendation(BaseModel):
    id: str
    scenario_id: str
    target_id: str
    proposal_id: str | None
    decision: RecommendationDecision
    status: RecommendationStatus
    confidence: float
    objective_score: float
    reason: str
    recommended_action: str
    source_shadow_ids: list[str]
    evidence: dict[str, Any]
    created_at: datetime
    updated_at: datetime
```

`target_id` examples:

```text
strategy.fast_window
strategy.constraints
writer.output_format
```

SQLite table:

```sql
CREATE TABLE IF NOT EXISTS version_recommendations (
    id TEXT PRIMARY KEY,
    scenario_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    proposal_id TEXT,
    decision TEXT NOT NULL,
    status TEXT NOT NULL,
    confidence REAL NOT NULL,
    objective_score REAL NOT NULL,
    reason TEXT NOT NULL,
    recommended_action TEXT NOT NULL,
    source_shadow_ids TEXT NOT NULL,
    evidence TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_version_recommendations_scenario
ON version_recommendations (scenario_id);

CREATE INDEX IF NOT EXISTS idx_version_recommendations_status
ON version_recommendations (status);
```

---

## Recommendation Rules

V3.3 rules must stay conservative:

```python
if no shadow results:
    INSUFFICIENT_EVIDENCE

if all evidence decisions are inconclusive:
    INSUFFICIENT_EVIDENCE

if latest/best evidence is synthetic:
    INSUFFICIENT_EVIDENCE

if guardrail violations exist:
    REJECT

if best evidence decision is WORSE:
    REJECT

if best evidence decision is IMPROVED and confidence >= min_confidence:
    RECOMMEND
```

Ranking:

```python
score = (
    evidence.confidence * 0.5
    + max(0.0, evidence.objective_score) * 0.3
    + min(1.0, sample_count / min_sample_count) * 0.2
)
```

Tie-breakers:

1. Higher `score`
2. Higher `confidence`
3. Higher `objective_score`
4. Newer `created_at`

---

### Task 1: Recommendation Models and Store

**Files:**
- Create: `checkpoint_ai/recommendation/models.py`
- Create: `checkpoint_ai/recommendation/store.py`
- Create: `checkpoint_ai/recommendation/__init__.py`
- Test: `tests/test_v33_version_recommender.py`

- [ ] **Step 1: Write failing store tests**

Create test:

```python
"""V3.3 version recommendation tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from checkpoint_ai.recommendation import (
    RecommendationDecision,
    RecommendationStatus,
    VersionRecommendation,
    VersionRecommendationStore,
)


class V33VersionRecommenderTest(unittest.TestCase):
    """Validate evidence-based version recommendations."""

    def test_recommendation_store_saves_lists_and_updates_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = VersionRecommendationStore(Path(tmp) / "recommendations.db")
            recommendation = VersionRecommendation(
                scenario_id="quant",
                target_id="strategy.fast_window",
                proposal_id="proposal-1",
                decision=RecommendationDecision.RECOMMEND,
                confidence=0.81,
                objective_score=0.22,
                reason="historical evidence improved with enough samples.",
                recommended_action="approve_for_shadow_or_paper",
                source_shadow_ids=["shadow-1"],
                evidence={"run_kind": "historical", "sample_count": 90},
            )

            store.save(recommendation)
            loaded = store.get(recommendation.id)
            listed = store.list(scenario_id="quant")
            updated = store.update_status(recommendation.id, RecommendationStatus.ACCEPTED)

            self.assertIsNotNone(loaded)
            self.assertEqual(loaded.decision, RecommendationDecision.RECOMMEND)
            self.assertEqual([item.id for item in listed], [recommendation.id])
            self.assertTrue(updated)
            self.assertEqual(store.get(recommendation.id).status, RecommendationStatus.ACCEPTED)
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m unittest tests/test_v33_version_recommender.py -v
```

Expected: FAIL with `ModuleNotFoundError: checkpoint_ai.recommendation`.

- [ ] **Step 3: Implement models and store**

Use Pydantic models for timestamps and JSON fields. Store `source_shadow_ids` and `evidence` as JSON text.

- [ ] **Step 4: Run tests**

Run:

```bash
python -m unittest tests/test_v33_version_recommender.py -v
```

Expected: PASS for store test.

---

### Task 2: VersionRecommender Core

**Files:**
- Create: `checkpoint_ai/recommendation/recommender.py`
- Modify: `checkpoint_ai/recommendation/__init__.py`
- Test: `tests/test_v33_version_recommender.py`

- [ ] **Step 1: Write failing recommender tests**

Add tests:

```python
def test_recommender_refuses_synthetic_shadow_results(self) -> None:
    # Save one ShadowResult with comparison_result.run_kind="synthetic" and improved=True.
    # VersionRecommender.recommend_for_scenario("quant") should store INSUFFICIENT_EVIDENCE.

def test_recommender_recommends_best_historical_improvement(self) -> None:
    # Save two ShadowResults:
    # - proposal-1 historical objective_score=0.08 confidence enough
    # - proposal-2 historical objective_score=0.22 confidence enough
    # It should recommend proposal-2.

def test_recommender_rejects_guardrail_violation(self) -> None:
    # Save one historical ShadowResult with guardrail_violations=["max_drawdown"].
    # It should store REJECT.
```

Use `ShadowResultStore` directly. Each `ShadowResult.comparison_result` should be a serialized `ComparisonResult.model_dump(mode="json")`.

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m unittest tests/test_v33_version_recommender.py -v
```

Expected: FAIL because `VersionRecommender` does not exist.

- [ ] **Step 3: Implement VersionRecommender**

Constructor:

```python
class VersionRecommender:
    def __init__(
        self,
        shadow_results: ShadowResultStore,
        recommendations: VersionRecommendationStore,
        evidence_engine: EvidenceEvaluationEngine | None = None,
        min_confidence: float = 0.6,
    ) -> None: ...
```

Methods:

```python
def recommend_for_scenario(self, scenario_id: str) -> VersionRecommendation:
    """Create and store the best recommendation for one scenario."""

def recommend_for_proposal(self, proposal_id: str) -> VersionRecommendation:
    """Create and store a recommendation for one proposal."""
```

Implementation:

1. Query shadow results.
2. Convert each `comparison_result` to `ComparisonResult`.
3. Evaluate with `EvidenceEvaluationEngine`.
4. Pick best candidate by ranking.
5. Store `VersionRecommendation`.

Target id:

```python
target_id = shadow.agent_id
```

If proposal metadata later provides `target_id`, use it in V3.4; do not add cross-store joins now.

- [ ] **Step 4: Run tests**

Run:

```bash
python -m unittest tests/test_v33_version_recommender.py -v
```

Expected: PASS.

---

### Task 3: Recommendation Reports

**Files:**
- Modify: `checkpoint_ai/reporting.py`
- Test: `tests/test_v33_version_recommender.py`

- [ ] **Step 1: Write failing report test**

Add:

```python
def test_report_generator_prints_recommendation_detail(self) -> None:
    # Store one VersionRecommendation.
    # ReportGenerator.recommendation(recommendation.id) includes:
    # decision, confidence, objective_score, reason, source_shadow_ids, evidence.
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
python -m unittest tests/test_v33_version_recommender.py -v
```

Expected: FAIL because `ReportGenerator.recommendation` does not exist.

- [ ] **Step 3: Implement report method**

Add to `ReportGenerator.__init__`:

```python
self.recommendations = VersionRecommendationStore(db_path)
```

Add:

```python
def recommendation(self, recommendation_id: str) -> str:
    ...
```

Report format:

```text
Recommendation Report

recommendation_id:
scenario_id:
target_id:
proposal_id:
decision:
status:
confidence:
objective_score:

为什么推荐/拒绝:
...

证据来源:
source_shadow_ids:
evidence:
```

- [ ] **Step 4: Run report tests**

Run:

```bash
python -m unittest tests/test_v33_version_recommender.py tests/test_v26_cli_report.py -v
```

Expected: PASS.

---

### Task 4: CLI Recommendation Commands

**Files:**
- Modify: `checkpoint_ai/v2_cli.py`
- Test: `tests/test_v33_version_recommender.py`

- [ ] **Step 1: Write failing CLI tests**

Use subprocess or direct parser call consistent with existing CLI tests. Commands:

```bash
python -m checkpoint_ai.cli --db <db> recommendation run --scenario-id quant
python -m checkpoint_ai.cli --db <db> recommendation list --scenario-id quant
python -m checkpoint_ai.cli --db <db> recommendation show <recommendation_id>
python -m checkpoint_ai.cli --db <db> recommendation accept <recommendation_id>
python -m checkpoint_ai.cli --db <db> recommendation reject <recommendation_id>
```

Expected readable output:

```text
Recommendation created:
decision:
confidence:
reason:
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
python -m unittest tests/test_v33_version_recommender.py -v
```

Expected: FAIL because command group does not exist.

- [ ] **Step 3: Add CLI parser and handlers**

Add `recommendation` subparser:

```text
recommendation run --scenario-id
recommendation list --scenario-id
recommendation show <id>
recommendation accept <id>
recommendation reject <id>
```

Use `VersionRecommender`, `VersionRecommendationStore`, and `ReportGenerator`.

Do not apply prompt/strategy changes from CLI in V3.3.

- [ ] **Step 4: Run CLI tests**

Run:

```bash
python -m unittest tests/test_v33_version_recommender.py -v
```

Expected: PASS.

---

### Task 5: Script and Blueprint Updates

**Files:**
- Modify: `scripts/run_v29_quant_data.py`
- Modify: `docs/V2.9_DATA_RUN_REPORT.md`
- Modify: `docs/BLUEPRINT.md`

- [ ] **Step 1: Update V2.9 data report script**

After shadow results are generated, instantiate `VersionRecommender` and run it for `quant-demo`.

Expected for synthetic data:

```text
- V3.3 recommendation decision: insufficient_evidence
- V3.3 recommendation reason: synthetic evidence cannot justify version recommendation.
```

- [ ] **Step 2: Run script**

Run:

```bash
python scripts/run_v29_quant_data.py
```

Expected:

```text
V2.9 quant data run complete: 30 runs
```

- [ ] **Step 3: Update BLUEPRINT**

Add:

```text
V3.3 = evidence-based version recommendation.
It recommends among existing versions/proposals only.
It does not generate new proposals or auto-apply.
Synthetic runs must produce insufficient_evidence.
```

---

### Task 6: Full Verification and Commit

**Files:**
- All files touched in V3.3.

- [ ] **Step 1: Run focused tests**

```bash
python -m unittest tests/test_v33_version_recommender.py -v
python -m unittest tests/test_v31_evidence_evaluation.py tests/test_v32_scenario_metric_schema.py -v
```

Expected: PASS.

- [ ] **Step 2: Run full quality gates**

```bash
python -m ruff check checkpoint_ai tests scripts examples
python -m mypy checkpoint_ai --show-error-codes --no-incremental
python -m unittest discover -s tests -v
```

Expected:

```text
All checks passed!
Success: no issues found
Ran ... tests
OK
```

- [ ] **Step 3: Commit and push**

```bash
git add checkpoint_ai/recommendation checkpoint_ai/reporting.py checkpoint_ai/v2_cli.py tests/test_v33_version_recommender.py scripts/run_v29_quant_data.py docs/BLUEPRINT.md docs/V2.9_DATA_RUN_REPORT.md
git commit -m "V3.3: Add evidence-based version recommender"
git push
```

---

## Design Review Notes

1. V3.3 is the first recommendation layer, not the first learning algorithm.
2. It should recommend only from existing evidence. It should not invent a new prompt, strategy, or parameter.
3. A recommendation is an auditable artifact, not an action. Human approval/application remains separate.
4. Synthetic runs must never produce `RECOMMEND`; they should produce `INSUFFICIENT_EVIDENCE`.
5. This module creates the data shape that V3.4/V3.5 can later use for Bandit or BO.

