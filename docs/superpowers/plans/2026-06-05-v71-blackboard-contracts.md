# V7.1 Blackboard Contracts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the V7 structured blackboard contracts and stores before any autonomous agent logic.

**Architecture:** Add small Pydantic models and SQLite stores for observations, safety findings, validation summaries, and loop state. These objects are the shared blackboard; Agents only read/write these contracts and never chat directly.

**Tech Stack:** Python 3, Pydantic, SQLite, unittest, ruff, mypy.

---

### Task 1: Observation Model And Store

**Files:**
- Create: `checkpoint_ai/learning/__init__.py`
- Create: `checkpoint_ai/learning/models.py`
- Create: `checkpoint_ai/learning/store.py`
- Test: `tests/test_v71_blackboard_contracts.py`

- [ ] Write failing tests for saving and querying `Observation` by `business_line_id`, `scenario_id`, and `status`.
- [ ] Run `python -m unittest tests/test_v71_blackboard_contracts.py -v` and verify import/store failures.
- [ ] Implement `Observation`, `ObservationStatus`, and `ObservationStore`.
- [ ] Re-run focused tests and confirm pass.

### Task 2: SafetyFinding And ValidationSummary Stores

**Files:**
- Modify: `checkpoint_ai/learning/models.py`
- Modify: `checkpoint_ai/learning/store.py`
- Test: `tests/test_v71_blackboard_contracts.py`

- [ ] Write failing tests for `SafetyFindingStore` and `ValidationSummaryStore`.
- [ ] Verify tests fail because stores do not exist.
- [ ] Implement `SafetyFinding`, `ValidationSummary`, and stores.
- [ ] Re-run focused tests and confirm pass.

### Task 3: Loop State Contract

**Files:**
- Modify: `checkpoint_ai/learning/models.py`
- Modify: `checkpoint_ai/learning/store.py`
- Test: `tests/test_v71_blackboard_contracts.py`

- [ ] Write failing tests proving `LearningLoopState` moves through explicit statuses.
- [ ] Implement state model and store.
- [ ] Reject cross-scenario state updates without explicit scenario id.
- [ ] Run focused tests.

### Task 4: Verification

**Commands:**
- `python -m unittest tests/test_v71_blackboard_contracts.py -v`
- `python -m unittest discover -s tests -v`
- `python -m ruff check checkpoint_ai tests scripts examples`
- `python -m mypy checkpoint_ai --show-error-codes --no-incremental`

- [ ] Run all commands.
- [ ] Fix failures before moving to V7.2.
