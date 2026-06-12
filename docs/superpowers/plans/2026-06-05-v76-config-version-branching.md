# V7.6 Config Version Branching Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let operators lock good configurations, continue optimization on a branch, or restart from a locked baseline.

**Architecture:** Versioning is first-class data, not a Hermes-only command. UI buttons and API endpoints operate on `ConfigVersion` and `ConfigBranch`; locked versions are immutable.

**Tech Stack:** Python 3, Pydantic, SQLite, FastAPI, React, unittest, TypeScript.

---

### Task 1: ConfigVersion And ConfigBranch Models

**Files:**
- Create: `loop_harness/config_version/__init__.py`
- Create: `loop_harness/config_version/models.py`
- Create: `loop_harness/config_version/store.py`
- Test: `tests/test_v76_config_version_branching.py`

- [ ] Write failing tests for saving config versions and branches.
- [ ] Implement immutable `ConfigVersion` with `locked` flag.
- [ ] Implement `ConfigBranch` with active branch state per business line / scenario.
- [ ] Run focused tests.

### Task 2: Lock / Branch / Switch / Rollback Service

**Files:**
- Create: `loop_harness/config_version/service.py`
- Test: `tests/test_v76_config_version_branching.py`

- [ ] Write failing tests for lock, branch, switch, rollback.
- [ ] Implement service methods.
- [ ] Ensure locked versions cannot be modified.
- [ ] Ensure branch operations stay scenario scoped.
- [ ] Run focused tests.

### Task 3: API Endpoints

**Files:**
- Modify: `loop_harness/api.py`
- Test: `tests/test_v76_config_version_branching.py`

- [ ] Write failing FastAPI tests for `/api/config/versions`, `/lock`, `/branch`, `/switch`, `/rollback`.
- [ ] Implement endpoints with stable error envelope.
- [ ] Record operator actions in `DecisionLog`.
- [ ] Run focused tests.

### Task 4: Web UI Buttons

**Files:**
- Modify: `web/src/types/api.ts`
- Modify: `web/src/api/client.ts`
- Create: `web/src/features/config/ConfigVersionPanel.tsx`
- Modify: relevant scenario or autonomy page once chosen
- Test: `web/tests/e2e/console.spec.ts`

- [ ] Add API client types.
- [ ] Add UI panel with Lock, Branch, Switch, Rollback actions.
- [ ] Require explicit confirmation for rollback.
- [ ] Add E2E shell/nav assertion if a new route is created.

### Task 5: Verification

**Commands:**
- `python -m unittest tests/test_v76_config_version_branching.py -v`
- `python -m unittest discover -s tests -v`
- `python -m ruff check loop_harness tests scripts examples`
- `python -m mypy loop_harness --show-error-codes --no-incremental`
- `npm run lint`
- `npm run format:check`
- `npm run build`

- [ ] Run all commands.
- [ ] Fix failures before moving to V7.7.
