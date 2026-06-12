# V7.3 Proposer Hive And Ranking Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate small, structured proposal candidates from observations and rank them before shadow/replay.

**Architecture:** Proposers are narrow candidate generators. They output generic `Proposal` records or candidate wrappers, but they never execute changes. Ranking and conflict detection are deterministic code.

**Tech Stack:** Python 3, Pydantic, SQLite, unittest.

---

### Task 1: Proposal Candidate Model

**Files:**
- Modify: `loop_harness/learning/models.py`
- Modify: `loop_harness/learning/store.py`
- Test: `tests/test_v73_proposer_hive_ranking.py`

- [ ] Write failing tests for `ProposalCandidate` persistence and scenario filtering.
- [ ] Implement candidate model with `observation_id`, `proposal_id`, `target_id`, `risk_hint`, `expected_metric`.
- [ ] Ensure candidate requires reason and expected metric.
- [ ] Run focused tests.

### Task 2: PromptProposer

**Files:**
- Create: `loop_harness/learning/proposers.py`
- Test: `tests/test_v73_proposer_hive_ranking.py`

- [ ] Write failing test where an observation about output clarity creates one prompt-slot patch candidate.
- [ ] Implement `PromptProposer`.
- [ ] Reject whole-prompt rewrite proposals.
- [ ] Run focused tests.

### Task 3: ParameterProposer

**Files:**
- Modify: `loop_harness/learning/proposers.py`
- Test: `tests/test_v73_proposer_hive_ranking.py`

- [ ] Write failing test where a metric observation creates a bounded parameter patch candidate.
- [ ] Implement `ParameterProposer`.
- [ ] Ensure parameter values stay inside provided guardrails.
- [ ] Run focused tests.

### Task 4: ConflictDetector And ProposalRanker

**Files:**
- Create: `loop_harness/learning/ranking.py`
- Test: `tests/test_v73_proposer_hive_ranking.py`

- [ ] Write failing tests for same-target conflict detection.
- [ ] Write failing tests for rank order: low risk, small patch, verifiable, historical success.
- [ ] Implement `ConflictDetector`.
- [ ] Implement `ProposalRanker`.
- [ ] Default to one candidate per target per round.

### Task 5: Verification

**Commands:**
- `python -m unittest tests/test_v73_proposer_hive_ranking.py -v`
- `python -m unittest discover -s tests -v`
- `python -m ruff check loop_harness tests scripts examples`
- `python -m mypy loop_harness --show-error-codes --no-incremental`

- [ ] Run all commands.
- [ ] Fix failures before moving to V7.4.
