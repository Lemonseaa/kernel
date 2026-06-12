# V7.5 Safety Monitor And Dynamic Balance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic guardrails that prevent overfitting, oscillation, regression, and budget blowups.

**Architecture:** Safety is code-first. `SafetyMonitor` explains and records findings, but hard blocking decisions come from deterministic guardrail, cooldown, budget, conflict, and regression checks.

**Tech Stack:** Python 3, Pydantic, SQLite, unittest.

---

### Task 1: Guardrail Rules

**Files:**
- Create: `loop_harness/learning/safety.py`
- Test: `tests/test_v75_safety_dynamic_balance.py`

- [ ] Write failing tests for parameter range, max patch magnitude, and blocked target rules.
- [ ] Implement `GuardrailRule` and `GuardrailEvaluator`.
- [ ] Ensure violation creates `SafetyFinding(blocked=True)`.
- [ ] Run focused tests.

### Task 2: Cooldown Rules

**Files:**
- Modify: `loop_harness/learning/safety.py`
- Test: `tests/test_v75_safety_dynamic_balance.py`

- [ ] Write failing test where same target cannot be changed again before N validations or T hours.
- [ ] Implement `CooldownRule`.
- [ ] Ensure different scenario / business line does not share cooldown.
- [ ] Run focused tests.

### Task 3: Budget Rules

**Files:**
- Modify: `loop_harness/learning/safety.py`
- Test: `tests/test_v75_safety_dynamic_balance.py`

- [ ] Write failing test where daily proposal/shadow budget blocks more attempts.
- [ ] Implement `OptimizationBudgetRule`.
- [ ] Read cost/attempt data from existing stores where possible.
- [ ] Run focused tests.

### Task 4: Regression Detection

**Files:**
- Modify: `loop_harness/learning/safety.py`
- Test: `tests/test_v75_safety_dynamic_balance.py`

- [ ] Write failing test where post-change metrics degrade beyond threshold.
- [ ] Implement `RegressionDetector`.
- [ ] Output rollback suggestion, not direct rollback.
- [ ] Run focused tests.

### Task 5: SafetyMonitor Summary

**Files:**
- Modify: `loop_harness/learning/safety.py`
- Modify: `loop_harness/reporting.py`
- Test: `tests/test_v75_safety_dynamic_balance.py`

- [ ] Write failing test that SafetyMonitor aggregates findings for one proposal.
- [ ] Implement `SafetyMonitor.evaluate_candidate`.
- [ ] Add safety section to report.
- [ ] Run focused tests.

### Task 6: Verification

**Commands:**
- `python -m unittest tests/test_v75_safety_dynamic_balance.py -v`
- `python -m unittest discover -s tests -v`
- `python -m ruff check loop_harness tests scripts examples`
- `python -m mypy loop_harness --show-error-codes --no-incremental`

- [ ] Run all commands.
- [ ] Fix failures before moving to V7.6.
