# V7.2 Observer Hive Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first observer hive so LoopHarness can automatically detect opportunities and anomalies from existing data.

**Architecture:** Implement narrow observer classes that read existing stores and write `Observation` records. Aggregation is deterministic code: dedupe, rank, filter noise, and emit top observations.

**Tech Stack:** Python 3, Pydantic, SQLite stores, unittest.

---

### Task 1: Observer Base Contract

**Files:**
- Create: `loop_harness/learning/observers.py`
- Test: `tests/test_v72_observer_hive.py`

- [ ] Write failing tests for `Observer` protocol and deterministic `ObserverResult`.
- [ ] Verify tests fail because observer module is missing.
- [ ] Implement the protocol and result types.
- [ ] Run focused tests.

### Task 2: MetricObserver

**Files:**
- Modify: `loop_harness/learning/observers.py`
- Test: `tests/test_v72_observer_hive.py`

- [ ] Write failing test where repeated failed or declining metric runs create one high-severity observation.
- [ ] Implement `MetricObserver` using `SummaryLogStore` and `MetricSchemaStore`.
- [ ] Ensure it does not infer direction without MetricSchema.
- [ ] Run focused tests.

### Task 3: DecisionObserver

**Files:**
- Modify: `loop_harness/learning/observers.py`
- Test: `tests/test_v72_observer_hive.py`

- [ ] Write failing test where repeated operator rejects create an observation about policy/prompt mismatch.
- [ ] Implement `DecisionObserver` using `DecisionLogStore`.
- [ ] Ensure mixed decisions below threshold produce no observation.
- [ ] Run focused tests.

### Task 4: ObservationAggregator

**Files:**
- Create: `loop_harness/learning/aggregation.py`
- Test: `tests/test_v72_observer_hive.py`

- [ ] Write failing tests for dedupe, severity ordering, and top-N filtering.
- [ ] Implement deterministic `ObservationAggregator`.
- [ ] Ensure it never merges observations across scenario boundaries.
- [ ] Run focused tests.

### Task 5: Verification

**Commands:**
- `python -m unittest tests/test_v72_observer_hive.py -v`
- `python -m unittest discover -s tests -v`
- `python -m ruff check loop_harness tests scripts examples`
- `python -m mypy loop_harness --show-error-codes --no-incremental`

- [ ] Run all commands.
- [ ] Fix failures before moving to V7.3.
