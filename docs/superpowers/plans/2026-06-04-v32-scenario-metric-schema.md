# V3.2 Scenario MetricSchema Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist scenario-specific metric schemas and surface V3.1 evidence decisions in human-readable reports.

**Architecture:** V3.2 keeps the V3.1 boundary: it evaluates evidence but does not recommend prompt/strategy versions. Metric schemas move from hardcoded/default registries into scenario-scoped storage, then shadow comparison and reports can use the right schema for each scenario. Reports become evidence-aware so synthetic data is not mistaken for real improvement.

**Tech Stack:** Python 3.13, Pydantic, SQLite, unittest, ruff, mypy.

---

## Scope

V3.2 does:

1. Persist `MetricSchema` per `scenario_id`.
2. Load scenario-specific schemas when comparing baseline vs shadow metrics.
3. Add report sections for `EvidenceDecision`, `RecommendedAction`, confidence, reason, run_kind, sample_count, and guardrail violations.
4. Add CLI commands to inspect and configure scenario metric schemas.
5. Update BLUEPRINT and V2.9 report to say V3.2 is about scenario metric contracts, not learning algorithms.

V3.2 does not:

1. Build Bandit, Bayesian Optimization, or auto recommendation.
2. Auto-generate PromptProposal.
3. Persist cross-scenario learning.
4. Promote strategies to paper/live.

---

## File Structure

Create:

- `checkpoint_ai/metrics/store.py`  
  SQLite-backed scenario metric schema store.

- `tests/test_v32_scenario_metric_schema.py`  
  V3.2 tests for persistence, comparison integration, report output, and CLI behavior.

Modify:

- `checkpoint_ai/metrics/__init__.py`  
  Export `MetricSchemaStore`.

- `checkpoint_ai/shadow/runner.py`  
  Accept optional `MetricSchemaStore` or schema resolver and use scenario-specific schemas.

- `checkpoint_ai/reporting.py`  
  Add evidence-aware proposal/shadow report output.

- `checkpoint_ai/v2_cli.py`  
  Add `metric-schema` commands.

- `scripts/run_v29_quant_data.py`  
  Save quant demo schemas to the store and include V3.2 schema source in report.

- `docs/BLUEPRINT.md`  
  Update current progress and V3.2 scope.

- `docs/V2.9_DATA_RUN_REPORT.md`  
  Regenerate after script run.

---

## Data Contract

Scenario metric schema storage should be explicit and simple:

```python
class MetricSchemaStore:
    def __init__(self, path: str | Path | None = None) -> None: ...

    def save_for_scenario(self, scenario_id: str, schemas: list[MetricSchema]) -> None: ...

    def list_for_scenario(self, scenario_id: str) -> list[MetricSchema]: ...

    def registry_for_scenario(self, scenario_id: str) -> MetricSchemaRegistry: ...

    def delete_for_scenario(self, scenario_id: str, metric_name: str | None = None) -> int: ...
```

SQLite table:

```sql
CREATE TABLE IF NOT EXISTS scenario_metric_schemas (
    scenario_id TEXT NOT NULL,
    name TEXT NOT NULL,
    direction TEXT NOT NULL,
    category TEXT NOT NULL,
    weight REAL NOT NULL,
    threshold REAL,
    is_guardrail INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (scenario_id, name)
);

CREATE INDEX IF NOT EXISTS idx_scenario_metric_schemas_scenario
ON scenario_metric_schemas (scenario_id);
```

Fallback rule:

```python
registry = metric_schema_store.registry_for_scenario(scenario_id)
if not registry.list():
    registry = MetricSchemaRegistry.default_quant() only when adapter_type == "quant_research_demo"
else:
    registry = MetricSchemaRegistry()
```

Do not silently use `default_quant()` for non-quant scenarios unless the caller explicitly asks for it.

---

### Task 1: MetricSchemaStore Persistence

**Files:**
- Create: `checkpoint_ai/metrics/store.py`
- Modify: `checkpoint_ai/metrics/__init__.py`
- Test: `tests/test_v32_scenario_metric_schema.py`

- [ ] **Step 1: Write failing persistence tests**

Add this test class:

```python
"""V3.2 scenario metric schema tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from checkpoint_ai.metrics import (
    MetricCategory,
    MetricDirection,
    MetricSchema,
    MetricSchemaStore,
)


class V32ScenarioMetricSchemaTest(unittest.TestCase):
    """Validate scenario-specific metric schemas."""

    def test_metric_schema_store_saves_and_loads_scenario_schemas(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = MetricSchemaStore(Path(tmp) / "schemas.db")
            store.save_for_scenario(
                "quant",
                [
                    MetricSchema(
                        name="sharpe",
                        direction=MetricDirection.HIGHER,
                        category=MetricCategory.BUSINESS,
                        weight=0.5,
                    ),
                    MetricSchema(
                        name="max_drawdown",
                        direction=MetricDirection.LOWER,
                        category=MetricCategory.GUARDRAIL,
                        weight=0.5,
                        threshold=0.2,
                        is_guardrail=True,
                    ),
                ],
            )

            loaded = store.list_for_scenario("quant")

            self.assertEqual([schema.name for schema in loaded], ["max_drawdown", "sharpe"])
            self.assertEqual(loaded[0].direction, MetricDirection.LOWER)
            self.assertTrue(loaded[0].is_guardrail)

    def test_metric_schema_store_isolates_scenarios(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = MetricSchemaStore(Path(tmp) / "schemas.db")
            store.save_for_scenario(
                "quant",
                [MetricSchema(name="sharpe", direction=MetricDirection.HIGHER)],
            )
            store.save_for_scenario(
                "content",
                [MetricSchema(name="readability", direction=MetricDirection.HIGHER)],
            )

            self.assertEqual([schema.name for schema in store.list_for_scenario("quant")], ["sharpe"])
            self.assertEqual([schema.name for schema in store.list_for_scenario("content")], ["readability"])
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m unittest tests/test_v32_scenario_metric_schema.py -v
```

Expected: FAIL with `ImportError: cannot import name 'MetricSchemaStore'`.

- [ ] **Step 3: Implement MetricSchemaStore**

Create `checkpoint_ai/metrics/store.py` with SQLite persistence. Use JSON-free columns because schemas are small and queryable. Convert enums with `.value` on write and enum constructors on read.

- [ ] **Step 4: Export MetricSchemaStore**

Modify `checkpoint_ai/metrics/__init__.py`:

```python
from checkpoint_ai.metrics.store import MetricSchemaStore
```

Add it to `__all__`.

- [ ] **Step 5: Run tests**

Run:

```bash
python -m unittest tests/test_v32_scenario_metric_schema.py -v
```

Expected: PASS.

---

### Task 2: ShadowRunner Uses Scenario Schemas

**Files:**
- Modify: `checkpoint_ai/shadow/runner.py`
- Test: `tests/test_v32_scenario_metric_schema.py`

- [ ] **Step 1: Write failing integration test**

Add a test that creates a custom schema where `risk` is lower-is-better and a guardrail. Run a shadow comparison where candidate risk is higher than baseline. Assert the stored `comparison_result.guardrail_violations` includes `risk`.

Test shape:

```python
def test_shadow_runner_uses_scenario_metric_schema_store(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "v32.db"
        schema_store = MetricSchemaStore(db_path)
        schema_store.save_for_scenario(
            "quant",
            [
                MetricSchema(
                    name="risk",
                    direction=MetricDirection.LOWER,
                    category=MetricCategory.GUARDRAIL,
                    weight=1.0,
                    threshold=0.1,
                    is_guardrail=True,
                )
            ],
        )
        # Use existing DummyAdapter or a tiny inline adapter fixture that returns metrics.
        # Baseline risk = 0.05, shadow risk = 0.2.
        # Assert comparison_result["guardrail_violations"] == ["risk"].
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
python -m unittest tests/test_v32_scenario_metric_schema.py -v
```

Expected: FAIL because `ShadowRunner` does not accept or use `MetricSchemaStore`.

- [ ] **Step 3: Update ShadowRunner constructor**

Add optional dependency:

```python
metric_schemas: MetricSchemaStore | None = None
```

Inside comparison:

```python
registry = (
    self.metric_schemas.registry_for_scenario(scenario_id)
    if self.metric_schemas is not None
    else MetricSchemaRegistry.default_quant()
)
```

If the registry is empty, use the current default behavior to avoid breaking existing tests.

- [ ] **Step 4: Run V2.4 and V3.2 tests**

Run:

```bash
python -m unittest tests/test_v24_shadow_runner.py tests/test_v32_scenario_metric_schema.py -v
```

Expected: PASS.

---

### Task 3: Evidence-Aware Reports

**Files:**
- Modify: `checkpoint_ai/reporting.py`
- Test: `tests/test_v32_scenario_metric_schema.py`

- [ ] **Step 1: Write failing report test**

Create a proposal with a stored shadow result containing `comparison_result`. Generate `ReportGenerator.proposal(proposal_id)`. Assert report includes:

```text
evidence_decision:
recommended_action:
confidence:
reason:
run_kind:
sample_count:
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
python -m unittest tests/test_v32_scenario_metric_schema.py -v
```

Expected: FAIL because report only prints `metric_diff`.

- [ ] **Step 3: Add evidence section to proposal report**

In `ReportGenerator.proposal`, when latest shadow has `comparison_result`, reconstruct:

```python
comparison = ComparisonResult(**latest_shadow.comparison_result)
evidence = EvidenceEvaluationEngine().evaluate(comparison)
```

Render:

```text
证据判断:
evidence_decision: inconclusive
recommended_action: collect_more_evidence
confidence: 0.6625
reason: synthetic evidence can validate the loop but cannot justify recommendation.
run_kind: synthetic
sample_count: 260
guardrail_violations: []
```

- [ ] **Step 4: Run report tests**

Run:

```bash
python -m unittest tests/test_v26_cli_report.py tests/test_v32_scenario_metric_schema.py -v
```

Expected: PASS.

---

### Task 4: CLI Metric Schema Commands

**Files:**
- Modify: `checkpoint_ai/v2_cli.py`
- Test: `tests/test_v32_scenario_metric_schema.py`

- [ ] **Step 1: Write failing CLI tests**

Test:

```bash
python -m checkpoint_ai.v2_cli metric-schema set --db <db> --scenario-id quant --name sharpe --direction higher --category business --weight 0.3
python -m checkpoint_ai.v2_cli metric-schema list --db <db> --scenario-id quant
```

Assert output includes:

```text
sharpe
higher
business
0.3
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
python -m unittest tests/test_v32_scenario_metric_schema.py -v
```

Expected: FAIL because command does not exist.

- [ ] **Step 3: Add CLI parser**

Add subcommands:

```text
metric-schema set
metric-schema list
metric-schema delete
metric-schema load-default-quant
```

Keep output readable. This CLI is for humans, not just JSON.

- [ ] **Step 4: Run CLI tests**

Run:

```bash
python -m unittest tests/test_v32_scenario_metric_schema.py -v
```

Expected: PASS.

---

### Task 5: V2.9 Script Uses Persisted Quant Schema

**Files:**
- Modify: `scripts/run_v29_quant_data.py`
- Modify: `docs/V2.9_DATA_RUN_REPORT.md`

- [ ] **Step 1: Update script**

After creating scenario, create `MetricSchemaStore(db_path)` and save `MetricSchemaRegistry.default_quant().list()` for scenario `quant-demo`.

Inject the store into `ShadowRunner`.

- [ ] **Step 2: Regenerate report**

Run:

```bash
python scripts/run_v29_quant_data.py
```

Expected:

```text
V2.9 quant data run complete: 30 runs
```

Report should include:

```text
- Scenario metric schema source: persisted scenario schema
- V3.1 evidence decisions: {'inconclusive/collect_more_evidence': 30}
```

---

### Task 6: Documentation and Verification

**Files:**
- Modify: `docs/BLUEPRINT.md`

- [ ] **Step 1: Update blueprint**

Add:

```text
V3.2 = Scenario MetricSchema persistence + evidence-aware report.
It does not do recommendation algorithms.
```

- [ ] **Step 2: Run full verification**

Run:

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

- [ ] **Step 3: Commit**

```bash
git add checkpoint_ai/metrics checkpoint_ai/shadow/runner.py checkpoint_ai/reporting.py checkpoint_ai/v2_cli.py tests/test_v32_scenario_metric_schema.py scripts/run_v29_quant_data.py docs/BLUEPRINT.md docs/V2.9_DATA_RUN_REPORT.md
git commit -m "V3.2: Persist scenario metric schemas"
git push
```

---

## Design Review Notes

1. The most important V3.2 decision is persistence of metric contracts. Without it, V3.3 cannot compare versions safely across scenarios.
2. Reports must show evidence state, not just metric deltas. A strong-looking synthetic Sharpe diff must still say `inconclusive`.
3. The CLI exists because humans need to inspect and edit scenario schemas without changing code.
4. The fallback behavior must be conservative. Non-quant scenarios should not accidentally inherit quant metric semantics.
5. This version deliberately avoids learning algorithms. V3.3 starts only after reports prove the evidence layer works.

