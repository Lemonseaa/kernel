# V7.4 Shadow Replay Scheduler And Validator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Automatically validate selected proposal candidates through shadow/replay and produce human-readable validation summaries.

**Architecture:** Scheduler invokes existing shadow/replay mechanisms and external adapter shadow support. Validator reads stored results and MetricSchema, then writes structured `ValidationSummary`; it does not execute or apply changes.

**Tech Stack:** Python 3, Pydantic, existing `ShadowRunner`, `ShadowResultStore`, `MetricSchemaStore`, unittest.

---

### Task 1: ShadowReplayJob Model

**Files:**
- Modify: `loop_harness/learning/models.py`
- Modify: `loop_harness/learning/store.py`
- Test: `tests/test_v74_shadow_replay_validator.py`

- [ ] Write failing tests for creating, listing, and completing `ShadowReplayJob`.
- [ ] Implement job statuses: `pending`, `running`, `succeeded`, `failed`, `cancelled`.
- [ ] Store `proposal_id`, `candidate_id`, `scenario_id`, `run_kind`.
- [ ] Run focused tests.

### Task 2: ShadowReplayScheduler

**Files:**
- Create: `loop_harness/learning/scheduler.py`
- Test: `tests/test_v74_shadow_replay_validator.py`

- [ ] Write failing test that a ranked candidate creates a pending shadow job.
- [ ] Write failing test that synthetic run_kind cannot be marked auto-queue eligible.
- [ ] Implement scheduler using existing stores.
- [ ] Run focused tests.

### Task 3: Validator

**Files:**
- Create: `loop_harness/learning/validator.py`
- Test: `tests/test_v74_shadow_replay_validator.py`

- [ ] Write failing test where improved business metrics create a positive `ValidationSummary`.
- [ ] Write failing test where guardrail violation creates a blocked summary.
- [ ] Implement metric direction aware summary using `MetricSchemaStore`.
- [ ] Ensure Validator writes recommendation: `approval`, `queue_candidate`, or `reject`.

### Task 4: Report Integration

**Files:**
- Modify: `loop_harness/reporting.py`
- Test: `tests/test_v74_shadow_replay_validator.py`

- [ ] Write failing test that proposal report includes latest validation summary.
- [ ] Add validation summary section to report output.
- [ ] Keep report readable and deterministic.

### Task 5: Verification

**Commands:**
- `python -m unittest tests/test_v74_shadow_replay_validator.py -v`
- `python -m unittest discover -s tests -v`
- `python -m ruff check loop_harness tests scripts examples`
- `python -m mypy loop_harness --show-error-codes --no-incremental`

- [ ] Run all commands.
- [ ] Fix failures before moving to V7.5.
