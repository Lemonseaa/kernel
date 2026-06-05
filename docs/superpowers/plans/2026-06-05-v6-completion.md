# V6 Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish V6 low-risk autonomy with operator-visible queue control, operator feedback suggestions, risk documentation, verification, and one final commit.

**Architecture:** Keep V6 conservative: the system can queue and audit low-risk actions, but the API processor remains audit-only until a real safe-apply backend exists. Operator feedback creates policy proposals that enter the existing Approval Inbox instead of inventing a second approval surface.

**Tech Stack:** Python 3, Pydantic, SQLite, FastAPI TestClient, React, TypeScript, TanStack Query, Tailwind, unittest.

---

### Task 1: Autonomy Queue API And Persistent Pause State

**Files:**
- Modify: `checkpoint_ai/autonomy/store.py`
- Modify: `checkpoint_ai/autonomy/queue.py`
- Modify: `checkpoint_ai/autonomy/__init__.py`
- Modify: `checkpoint_ai/api.py`
- Test: `tests/test_v66_autonomy_console_api.py`

- [ ] Write failing API tests for list/detail/status/pause/resume/process.
- [ ] Verify tests fail because routes and persistent queue state are missing.
- [ ] Add `AutonomyQueueStateStore` and wire it into `AutoActionQueue`.
- [ ] Add FastAPI endpoints under `/api/autonomy`.
- [ ] Run focused tests and keep V6.1/V6.4 tests green.

### Task 2: Autonomy Web Console Page

**Files:**
- Modify: `web/src/types/api.ts`
- Modify: `web/src/api/client.ts`
- Modify: `web/src/app/App.tsx`
- Modify: `web/src/layout/Layout.tsx`
- Create: `web/src/features/autonomy/AutonomyPage.tsx`
- Modify: `web/tests/e2e/console.spec.ts`

- [ ] Write/update e2e assertion for the Autonomy nav link.
- [ ] Add API types and client methods.
- [ ] Add an operator page for status, pause/resume, action list, and audit-only process.
- [ ] Wire `/autonomy` route and navigation.
- [ ] Run frontend lint/build/e2e during final verification.

### Task 3: Operator Feedback Loop

**Files:**
- Modify: `checkpoint_ai/prompt/models.py`
- Create: `checkpoint_ai/autonomy/feedback.py`
- Modify: `checkpoint_ai/autonomy/__init__.py`
- Test: `tests/test_v65_operator_feedback_loop.py`

- [ ] Write failing tests proving repeated approve/reject decisions create a policy proposal.
- [ ] Add `ProposalKind.POLICY` and `ProposalTargetType.POLICY_RULE`.
- [ ] Implement `OperatorFeedbackAnalyzer` that reads `DecisionLogStore` and returns a generic policy `Proposal`.
- [ ] Verify policy proposals appear in `ApprovalInbox`.

### Task 4: V6 Stable Docs And Risk Sweep

**Files:**
- Modify: `docs/V6_PLAN.md`
- Create: `docs/V6_RISK_REVIEW.md`
- Create: `docs/V6_STABLE_ACCEPTANCE.md`
- Modify: `docs/BLUEPRINT.md`

- [ ] Update V6 plan status.
- [ ] Document residual risks and explicit non-goals.
- [ ] Add acceptance evidence checklist.
- [ ] Keep blueprint navigation consistent.

### Task 5: Full Verification And Commit

**Commands:**
- `python -m unittest discover -s tests -v`
- `python -m ruff check checkpoint_ai tests scripts examples`
- `python -m mypy checkpoint_ai --show-error-codes --no-incremental`
- `python -m compileall checkpoint_ai`
- `npm run lint`
- `npm run format:check`
- `npm run build`
- `npm run e2e`
- `git diff --check`

- [ ] Run all verification fresh.
- [ ] Fix every failure before claiming completion.
- [ ] Review `git diff --stat` and `git status`.
- [ ] Commit and push with a V6 completion message.
