# V4 Isolation and Adapter Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make CheckpointAI reliable across multiple scenarios and multiple adapters without cross-contamination, premature third-party integrations, or fake cross-scenario learning.

**Architecture:** V4 hardens scenario isolation first, then adds adapter capability metadata and compatibility evaluation. Cross-scenario insight is preview-only: it can surface possible patterns but cannot migrate prompts, parameters, strategies, or policies. V4 deliberately does not implement full TradingAgents/CrewAI adapters; it creates the contract that tells us whether such adapters are worth building.

**Tech Stack:** Python 3.13, Pydantic, SQLite, unittest, ruff, mypy, Markdown docs.

---

## V4 Positioning

V3 proves:

- Evidence can be judged conservatively.
- Scenario metric schemas can be persisted.
- Existing versions/proposals can be recommended from evidence.
- Continuous parameter suggestions can be generated as a spike.

V4 must prove:

- Multiple scenarios can run side by side without data leakage.
- Multiple adapters can coexist and declare capabilities honestly.
- Unsupported adapter capabilities degrade explicitly instead of failing silently.
- External adapter candidates can be evaluated before we write integration code.
- Cross-scenario insights are visible but cannot auto-migrate behavior.

V4 should not prove:

- TradingAgents is fully integrated.
- CrewAI is fully integrated.
- Cross-scenario learning improves results.
- Marketplace/plugin system is ready.
- Multi-tenant enterprise isolation is complete.

---

## Version Breakdown

| Version | Name | Core Proof |
|---|---|---|
| V4.1 | Scenario Isolation Hardening | Every query and artifact is scenario-scoped by default |
| V4.2 | AdapterRegistry Hardening | Adapters declare capabilities and unsupported features degrade explicitly |
| V4.3 | Adapter Compatibility Contract | We can decide whether an external Agent framework is worth adapting before coding |
| V4.4 | Cross-Scenario Insight Preview | We can surface possible patterns without migrating anything |
| V4.5 | V4 Stable | Multi-scenario, multi-adapter infrastructure works end to end |

Optional:

| Spike | Name | Purpose |
|---|---|---|
| V4 Spike | TradingAgents/CrewAI Compatibility Study | Produce go/no-go report, not production adapter code |

---

## Non-Negotiable Boundaries

1. **No automatic cross-scenario migration.**  
   Cross-scenario insight can only say “this may be related.”

2. **No third-party deep fork.**  
   TradingAgents/CrewAI adaptation must be contract-first, not “start hacking until it runs.”

3. **No hidden global query.**  
   Stores should require explicit opt-in for cross-scenario queries.

4. **No fake capability.**  
   If an adapter does not support shadow run, prompt injection, metrics capture, trace capture, or continuous params, the system must say so.

5. **No learning claim from weak evidence.**  
   Cross-scenario insight must reject underpowered comparisons.

---

## File Structure

Create:

- `checkpoint_ai/isolation/`
  - `__init__.py`
  - `scope.py`
  - `auditor.py`

- `checkpoint_ai/adapter/capabilities.py`
  - `AdapterCapabilities`
  - `CapabilitySupport`
  - downgrade/rejection reason helpers

- `checkpoint_ai/adapter/compatibility.py`
  - `AdapterCompatibilityChecklist`
  - `AdapterCompatibilityReport`
  - `AdapterCompatibilityEvaluator`

- `checkpoint_ai/insights/`
  - `__init__.py`
  - `cross_scenario.py`
  - `store.py`

- `docs/adapter_checklist.md`
  - Living checklist for TradingAgents/CrewAI/Dify-style tools.

- `docs/V4_PLAN.md`
  - Human-readable V4 summary for Hermes discussion and future execution.

Add tests:

- `tests/test_v41_scenario_isolation.py`
- `tests/test_v42_adapter_registry.py`
- `tests/test_v43_adapter_compatibility.py`
- `tests/test_v44_cross_scenario_insights.py`
- `tests/test_v45_v4_stable.py`

Modify:

- `checkpoint_ai/adapter/base.py`
- `checkpoint_ai/adapter/registry.py`
- `checkpoint_ai/adapter/dummy_adapter.py`
- `checkpoint_ai/adapter/opc_agent_adapter.py`
- `checkpoint_ai/adapter/quant_research_adapter.py`
- `checkpoint_ai/scenario/store.py`
- `checkpoint_ai/logs/raw_log.py`
- `checkpoint_ai/logs/summary_log.py`
- `checkpoint_ai/shadow/store.py`
- `checkpoint_ai/recommendation/store.py`
- `checkpoint_ai/optimization/store.py`
- `checkpoint_ai/v2_cli.py`
- `checkpoint_ai/reporting.py`
- `docs/BLUEPRINT.md`

---

## V4.1: Scenario Isolation Hardening

### Intent

Current stores often support `query_by_scenario`, but the system does not have one shared isolation contract. V4.1 makes scenario isolation explicit and auditable.

### Acceptance Criteria

1. Raw logs, summary logs, shadow results, recommendations, metric schemas, parameter suggestions, prompt versions, and proposals are all scenario-scoped.
2. Scenario-scoped list/query methods are the default for human-facing workflows.
3. Cross-scenario query requires an explicit flag or method name containing `cross_scenario`.
4. Scenario archive/delete does not delete unrelated scenario data.
5. Isolation auditor can detect store rows missing scenario_id or using unexpected scenario_id.

### Implementation Tasks

#### Task V4.1.1: Scenario Scope Model

**Files:**
- Create: `checkpoint_ai/isolation/scope.py`
- Create: `checkpoint_ai/isolation/__init__.py`
- Test: `tests/test_v41_scenario_isolation.py`

- [ ] Write failing test:

```python
from checkpoint_ai.isolation import ScenarioScope

def test_scenario_scope_requires_explicit_cross_scenario_flag():
    scope = ScenarioScope(scenario_id="quant")
    assert scope.scenario_id == "quant"
    assert scope.allow_cross_scenario is False

    cross = ScenarioScope.cross_scenario(reason="admin audit")
    assert cross.allow_cross_scenario is True
    assert cross.reason == "admin audit"
```

- [ ] Implement:

```python
class ScenarioScope(BaseModel):
    scenario_id: str | None = None
    allow_cross_scenario: bool = False
    reason: str | None = None

    @classmethod
    def cross_scenario(cls, reason: str) -> "ScenarioScope":
        if not reason.strip():
            raise ValueError("cross-scenario scope requires reason")
        return cls(allow_cross_scenario=True, reason=reason)
```

#### Task V4.1.2: Isolation Auditor

**Files:**
- Create: `checkpoint_ai/isolation/auditor.py`
- Test: `tests/test_v41_scenario_isolation.py`

- [ ] Write failing test that creates rows for two scenarios in RawLogStore, SummaryLogStore, ShadowResultStore, VersionRecommendationStore, and ParameterSuggestionStore, then confirms auditor reports both scenario ids and no missing scenario ids.

- [ ] Implement `ScenarioIsolationAuditor`:

```python
class IsolationCheckResult(BaseModel):
    store_name: str
    scenario_ids: list[str]
    missing_scenario_id_count: int
    status: Literal["ok", "warning"]

class ScenarioIsolationAuditor:
    def audit_sqlite(self, db_path: str | Path) -> list[IsolationCheckResult]:
        ...
```

Audited tables:

```text
raw_logs
summary_logs
shadow_results
prompt_proposals
proposals
prompt_versions
scenario_metric_schemas
version_recommendations
parameter_suggestions
agent_loops
```

Tables that do not exist should be skipped, not treated as failure.

#### Task V4.1.3: CLI Isolation Audit

**Files:**
- Modify: `checkpoint_ai/v2_cli.py`
- Test: `tests/test_v41_scenario_isolation.py`

- [ ] Add CLI:

```bash
checkpointai isolation audit --db <db>
```

Expected output:

```text
Scenario Isolation Audit
raw_logs    ok      scenarios=quant,content    missing=0
...
```

This is an operations tool, not a data export.

---

## V4.2: AdapterRegistry Hardening

### Intent

Current `AdapterRegistry` can register and resolve adapters. V4.2 makes adapter capabilities first-class and prevents the system from pretending unsupported operations are available.

### Acceptance Criteria

1. Every adapter exposes structured capabilities.
2. Registry can list adapters with capabilities.
3. Registry can answer whether an adapter supports a capability.
4. ShadowRunner checks `shadow_run` support and returns a clear failure if unsupported.
5. Prompt update/prompt injection paths check `prompt_injection` support.
6. Continuous parameter optimizer paths check `continuous_params` support when attached to an adapter.

### Capability Model

```python
class CapabilitySupport(str, Enum):
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    PARTIAL = "partial"

class AdapterCapabilities(BaseModel):
    prompt_injection: CapabilitySupport = CapabilitySupport.UNSUPPORTED
    metrics_capture: CapabilitySupport = CapabilitySupport.UNSUPPORTED
    shadow_run: CapabilitySupport = CapabilitySupport.UNSUPPORTED
    run_trace: CapabilitySupport = CapabilitySupport.UNSUPPORTED
    continuous_params: CapabilitySupport = CapabilitySupport.UNSUPPORTED
    structured_input: CapabilitySupport = CapabilitySupport.SUPPORTED
    structured_output: CapabilitySupport = CapabilitySupport.SUPPORTED
    notes: dict[str, str] = Field(default_factory=dict)
```

### Implementation Tasks

#### Task V4.2.1: Structured Adapter Capabilities

**Files:**
- Create: `checkpoint_ai/adapter/capabilities.py`
- Modify: `checkpoint_ai/adapter/base.py`
- Modify built-in adapters.
- Test: `tests/test_v42_adapter_registry.py`

- [ ] Write failing test:

```python
def test_adapter_capabilities_are_structured():
    adapter = DummyAdapter()
    caps = adapter.capabilities()
    assert caps.metrics_capture == CapabilitySupport.SUPPORTED
    assert caps.structured_input == CapabilitySupport.SUPPORTED
```

- [ ] Implement backwards-compatible helper:

```python
def normalize_capabilities(raw: AdapterCapabilities | dict[str, bool]) -> AdapterCapabilities:
    ...
```

This avoids breaking older adapters immediately.

#### Task V4.2.2: Registry Capability Queries

**Files:**
- Modify: `checkpoint_ai/adapter/registry.py`
- Test: `tests/test_v42_adapter_registry.py`

- [ ] Add:

```python
def capabilities_for(self, adapter_type: str) -> AdapterCapabilities: ...
def supports(self, adapter_type: str, capability: str) -> bool: ...
def describe(self) -> list[AdapterDescription]: ...
```

- [ ] Tests:

```python
assert registry.supports("dummy_stock_signal", "metrics_capture")
assert not registry.supports("dummy_stock_signal", "continuous_params")
```

#### Task V4.2.3: Explicit Degradation

**Files:**
- Modify: `checkpoint_ai/shadow/runner.py`
- Test: `tests/test_v42_adapter_registry.py`

- [ ] Create fixture adapter with `shadow_run=unsupported`.
- [ ] Run ShadowRunner.
- [ ] Assert stored/returned ShadowResult:

```python
status == "failed"
passed is False
error_type == "unsupported_capability"
value_summary includes "shadow_run unsupported"
```

---

## V4.3: Adapter Compatibility Contract

### Intent

Before adapting TradingAgents/CrewAI, evaluate whether the framework exposes enough structure to be useful. This prevents sunk cost.

### Acceptance Criteria

1. `docs/adapter_checklist.md` exists and is the living checklist.
2. Compatibility evaluator can score candidate adapters.
3. It can produce a Markdown report.
4. TradingAgents/CrewAI can be evaluated by metadata without writing integration code.
5. Checklist result is go/no-go/needs-spike.

### Checklist Categories

```text
Input/Output
- structured input
- structured output

Prompt Control
- prompt slots exposed
- prompt injection supported

Execution
- shadow run supported
- run trace available

Metrics
- metrics capture supported
- metric format compatible

Integration Effort
- estimated days
- dependencies
- required code ownership
```

### Implementation Tasks

#### Task V4.3.1: Compatibility Models

**Files:**
- Create: `checkpoint_ai/adapter/compatibility.py`
- Test: `tests/test_v43_adapter_compatibility.py`

- [ ] Define:

```python
class AdapterCompatibilityDecision(str, Enum):
    GO = "go"
    NO_GO = "no_go"
    NEEDS_SPIKE = "needs_spike"

class AdapterCompatibilityInput(BaseModel):
    name: str
    structured_input: bool
    structured_output: bool
    prompt_slots: bool
    prompt_injection: bool
    shadow_run: bool
    run_trace: bool
    metrics_capture: bool
    metric_format_compatible: bool
    estimated_days: int
    dependencies: list[str] = []

class AdapterCompatibilityReport(BaseModel):
    name: str
    score: float
    decision: AdapterCompatibilityDecision
    blockers: list[str]
    warnings: list[str]
    markdown: str
```

- [ ] Rules:

```text
NO_GO if structured_input or structured_output is false.
NO_GO if metrics_capture is false.
NEEDS_SPIKE if estimated_days > 5.
NEEDS_SPIKE if prompt_slots or run_trace missing.
GO only when score >= 0.75 and no blockers.
```

#### Task V4.3.2: Checklist Document

**Files:**
- Create: `docs/adapter_checklist.md`

Content must include:

```markdown
# Adapter Compatibility Checklist

## Purpose
Decide whether an external Agent framework is worth adapting before writing adapter code.

## Required Fields
...

## Decision Rules
...

## Candidate Reports
### TradingAgents
Status: not evaluated

### CrewAI
Status: not evaluated
```

#### Task V4.3.3: CLI Compatibility Report

**Files:**
- Modify: `checkpoint_ai/v2_cli.py`
- Test: `tests/test_v43_adapter_compatibility.py`

Command:

```bash
checkpointai adapter compatibility \
  --name TradingAgents \
  --structured-input true \
  --structured-output true \
  --prompt-slots false \
  --prompt-injection false \
  --shadow-run false \
  --run-trace true \
  --metrics-capture true \
  --metric-format-compatible false \
  --estimated-days 8
```

Expected:

```text
Adapter Compatibility Report
decision: needs_spike
blockers:
warnings:
```

---

## V4.4: Cross-Scenario Insight Preview

### Intent

Show possible related learnings across scenarios without migrating anything.

### Acceptance Criteria

1. Can compare scenario metric schemas and recommendation patterns.
2. Can generate `CrossScenarioInsight` records.
3. Insight includes source scenario, target scenario, similarity reason, risk, and rejection reason if not generated.
4. No prompt/parameter/policy migration API exists in V4.4.
5. Reject insight if data is too small or metrics are not comparable.

### Rejection Criteria

Do not suggest cross-scenario insight when:

```text
- Source or target scenario has fewer than 20 runs
- Metrics are not comparable
- Domain similarity score < threshold
- Confounding factors are detected but uncontrolled
- Any source recommendation is based only on synthetic evidence
```

### Implementation Tasks

#### Task V4.4.1: Insight Models

**Files:**
- Create: `checkpoint_ai/insights/cross_scenario.py`
- Create: `checkpoint_ai/insights/__init__.py`
- Test: `tests/test_v44_cross_scenario_insights.py`

Models:

```python
class CrossScenarioInsightDecision(str, Enum):
    SUGGEST = "suggest"
    REJECT = "reject"

class CrossScenarioInsight(BaseModel):
    id: str
    source_scenario_id: str
    target_scenario_id: str
    decision: CrossScenarioInsightDecision
    similarity_score: float
    reason: str
    risk: str
    source_evidence_ids: list[str]
    rejection_reasons: list[str]
```

#### Task V4.4.2: Insight Generator

**Files:**
- Create: `checkpoint_ai/insights/store.py`
- Modify: `checkpoint_ai/insights/cross_scenario.py`
- Test: `tests/test_v44_cross_scenario_insights.py`

Inputs:

```python
class ScenarioInsightInput(BaseModel):
    scenario_id: str
    domain_tags: list[str]
    metric_names: list[str]
    run_count: int
    non_synthetic_recommendation_count: int
```

Rules:

```text
run_count < 20 -> reject
shared metric ratio < 0.5 -> reject
domain tag overlap < 0.3 -> reject
non_synthetic_recommendation_count == 0 -> reject
otherwise suggest
```

#### Task V4.4.3: Report and CLI

**Files:**
- Modify: `checkpoint_ai/reporting.py`
- Modify: `checkpoint_ai/v2_cli.py`
- Test: `tests/test_v44_cross_scenario_insights.py`

Commands:

```bash
checkpointai insight compare --source quant --target content --source-tags quant,research --target-tags quant,content --source-metrics sharpe,drawdown --target-metrics sharpe,readability --source-runs 30 --target-runs 30 --source-non-synthetic-recommendations 1 --target-non-synthetic-recommendations 1
checkpointai insight list
checkpointai report insight <insight_id>
```

Report must say:

```text
This is an observation only. It does not migrate prompt, parameter, strategy, or policy.
```

---

## V4.5: V4 Stable

### Intent

Prove the V4 infrastructure works together.

### Acceptance Criteria

1. Two scenarios can coexist with different adapters and metric schemas.
2. Queries and reports are scoped by scenario by default.
3. Adapter capabilities are visible.
4. Unsupported capabilities degrade explicitly.
5. Compatibility checklist can evaluate an external adapter candidate.
6. Cross-scenario insight preview can suggest or reject with reasons.
7. No automatic cross-scenario migration exists.

### End-to-End Test

**Files:**
- Test: `tests/test_v45_v4_stable.py`

Test flow:

```python
def test_v4_stable_multi_scenario_multi_adapter_flow():
    # create quant scenario with QuantResearchDemoAdapter
    # create content scenario with DummyAdapter
    # save distinct metric schemas
    # run each adapter
    # create shadow result in quant
    # create recommendation in quant
    # verify content query cannot see quant shadow/recommendation by default
    # run adapter compatibility evaluation for TradingAgents-like metadata
    # run cross-scenario insight; it should reject if metrics are not comparable
```

### Final Verification

Run:

```bash
python -m ruff check checkpoint_ai tests scripts examples
python -m mypy checkpoint_ai --show-error-codes --no-incremental
python -m unittest discover -s tests -v
python scripts/run_v29_quant_data.py
```

Expected:

```text
All checks passed!
Success: no issues found
Ran ... tests
OK
V2.9 quant data run complete: 30 runs
```

---

## V4 Spike: TradingAgents/CrewAI Compatibility Study

This is optional and should not block V4.5.

### Goal

Decide whether TradingAgents or CrewAI is worth adapting.

### Output

Create:

- `docs/adapter_reports/tradingagents.md`
- `docs/adapter_reports/crewai.md`

Each report:

```markdown
# Adapter Compatibility Report: TradingAgents

## Decision
go / no_go / needs_spike

## What It Exposes
...

## What It Does Not Expose
...

## Required Work
...

## Recommendation
...
```

### Rule

No adapter code before report. If report is `no_go`, do not write adapter.

---

## Design Risks

### Risk 1: V4 becomes enterprise multi-tenant work

Avoid this. V4 scenario isolation is local system safety, not SaaS tenancy.

### Risk 2: Adapter compatibility turns into framework shopping

Avoid this. Compatibility reports answer “should we use this for a workflow node?” not “is this repo impressive?”

### Risk 3: Cross-scenario insight becomes fake transfer learning

Avoid this. V4.4 is observation-only and must reject underpowered comparisons.

### Risk 4: Capability metadata lies

Mitigation: built-in adapters must have tests proving capability behavior. Unsupported capability must produce explicit failure, not silent success.

### Risk 5: Too many CLI commands

Mitigation: keep commands human-readable and operational. V5 Console can later wrap them.

---

## Recommended V4 Execution Order

1. V4.1 Scenario Isolation Hardening
2. V4.2 AdapterRegistry Hardening
3. V4.3 Adapter Compatibility Contract
4. V4.4 Cross-Scenario Insight Preview
5. V4.5 V4 Stable
6. Optional V4 Spike for TradingAgents/CrewAI

Do not start V4.4 before V4.1 is complete. Cross-scenario insight without reliable scenario isolation is dangerous.

---

## Discussion Questions for Hermes

1. Should V4.1 add archive/delete lifecycle to `Scenario`, or keep lifecycle in BusinessLine only?
2. Should cross-scenario insight require manual input tags, or infer tags from scenario descriptions?
3. Should adapter compatibility reports be pure docs, or should they be stored in SQLite too?
4. Should V4.2 force all adapters to return `AdapterCapabilities`, or keep dict compatibility for one more version?
5. Is V4 Spike worth doing before V4.3, or after V4.5 stable?

