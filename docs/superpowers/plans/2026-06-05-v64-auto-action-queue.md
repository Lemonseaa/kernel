# V6.4 Auto Action Queue Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first V6.4 backend queue processor for low-risk autonomous actions.

**Architecture:** Reuse `AutonomyActionStore` as the queue store. Add a focused `AutoActionQueue` service that can pause, resume, process the next pending action through an injected handler, and write `DecisionLog` records for success/failure. This phase does not implement real prompt/strategy apply and does not add Web UI.

**Tech Stack:** Python, Pydantic, SQLite, unittest.

---

## Scope

This phase implements only V6.4 backend queue mechanics:

- Pending action selection
- Pause/resume state
- `process_next()` lifecycle
- Success/failure transition
- Decision log audit

This phase does not implement:

- Web Console queue view
- Real adapter safe-apply execution
- Policy feedback learning
- TradingAgents integration
- Live/paper deployment

## Files

- Create: `checkpoint_ai/autonomy/queue.py`
- Modify: `checkpoint_ai/autonomy/__init__.py`
- Test: `tests/test_v64_auto_action_queue.py`
- Update: `docs/V6_PLAN.md`

## Task 1: Queue Processor Contract

- [ ] **Step 1: Write failing tests**

Create `tests/test_v64_auto_action_queue.py` with tests for:

```python
def test_queue_processes_next_pending_action_and_records_success(self):
    store = AutonomyActionStore(db_path)
    decisions = DecisionLogStore(db_path)
    action = store.create(
        scenario_id="demo-quant",
        proposal_id="proposal-1",
        action_type="prompt_patch",
        checkpoint_id="checkpoint-1",
        reason="Low-risk historical shadow passed.",
    )
    queue = AutoActionQueue(actions=store, decisions=decisions)

    processed = queue.process_next(lambda item: {"applied": item.proposal_id})

    self.assertEqual(processed.id, action.id)
    self.assertEqual(store.get(action.id).status, AutonomyActionStatus.SUCCEEDED)
    self.assertEqual(decisions.list(source_id=action.id)[0].kind, DecisionKind.SYSTEM)
```

Expected failure: `ImportError: cannot import name 'AutoActionQueue'`.

- [ ] **Step 2: Implement `AutoActionQueue.process_next()`**

Create `checkpoint_ai/autonomy/queue.py`:

```python
class AutoActionQueue:
    def __init__(self, actions: AutonomyActionStore, decisions: DecisionLogStore) -> None:
        self.actions = actions
        self.decisions = decisions
        self._paused = False

    def process_next(self, handler: Callable[[AutonomyActionLog], dict[str, Any]]) -> AutonomyActionLog | None:
        ...
```

Rules:

- Return `None` when paused.
- Return `None` when no pending actions.
- Set action to `RUNNING` before handler.
- On success, set `SUCCEEDED`, store handler result, write `DecisionKind.SYSTEM`.
- On exception, set `FAILED`, store `error`, write `DecisionKind.ERROR`, return failed action.

- [ ] **Step 3: Export queue service**

Modify `checkpoint_ai/autonomy/__init__.py` to export `AutoActionQueue`.

- [ ] **Step 4: Run focused tests**

Run:

```bash
python -m unittest tests/test_v64_auto_action_queue.py -v
```

Expected: all V6.4 queue tests pass.

## Task 2: Pause / Resume

- [ ] **Step 1: Write failing tests**

Add tests:

```python
def test_queue_pause_prevents_processing_until_resume(self):
    queue.pause()
    self.assertIsNone(queue.process_next(lambda item: {"applied": True}))
    queue.resume()
    self.assertIsNotNone(queue.process_next(lambda item: {"applied": True}))
```

Expected failure: `AutoActionQueue` has no `pause`.

- [ ] **Step 2: Implement lifecycle controls**

Add:

```python
def pause(self) -> None
def resume(self) -> None
def is_paused(self) -> bool
```

- [ ] **Step 3: Run focused tests**

Run:

```bash
python -m unittest tests/test_v64_auto_action_queue.py -v
```

Expected: all queue tests pass.

## Task 3: Documentation And Verification

- [ ] **Step 1: Update `docs/V6_PLAN.md`**

Mark V6.4 backend queue processor as started/completed for backend, and state that Web Console queue view remains next.

- [ ] **Step 2: Run checks**

Run:

```bash
python -m unittest tests/test_v61_systemic_risk_fixes.py tests/test_v64_auto_action_queue.py -v
python -m ruff check checkpoint_ai tests scripts examples
python -m mypy checkpoint_ai --show-error-codes --no-incremental
```

Expected:

- V6.1 and V6.4 tests pass.
- Ruff passes.
- Mypy passes.

## Self-Review

- This plan covers V6.4 backend queue processing only.
- It does not skip audit logging.
- It does not add UI before queue semantics are stable.
- It does not implement real production apply.
