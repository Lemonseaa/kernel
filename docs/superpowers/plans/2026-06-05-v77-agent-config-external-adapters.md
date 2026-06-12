# V7.7 Agent Config And External Adapter Management Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let each business line configure its internal optimization agents, connect multiple external agent systems, and inject only human-confirmed preferences into Agent context.

**Architecture:** Agent config is scoped by business line, role, and config version. External systems are registered as connections; the internal optimization system targets connections through adapters, not direct imports. Human preferences live in Markdown profiles: Hermes can generate suggested notes, but only `USER_PROFILE.md` is formal input for Agents.

**Tech Stack:** Python 3, Pydantic, SQLite, FastAPI, React, unittest, TypeScript.

---

### Task 1: AgentConfig Model And Store

**Files:**
- Create: `loop_harness/agent_config/__init__.py`
- Create: `loop_harness/agent_config/models.py`
- Create: `loop_harness/agent_config/store.py`
- Test: `tests/test_v77_agent_config_external_adapters.py`

- [ ] Write failing tests for saving and listing configs by business line, role, and config version.
- [ ] Implement `AgentConfig` with `skills`, `tools`, `mcp_servers`, `triggers`, `constraints`, `model`.
- [ ] Reject configs missing business line or role.
- [ ] Run focused tests.

### Task 2: ExternalAgentConnection Model

**Files:**
- Create: `loop_harness/external_agents/__init__.py`
- Create: `loop_harness/external_agents/models.py`
- Create: `loop_harness/external_agents/store.py`
- Test: `tests/test_v77_agent_config_external_adapters.py`

- [ ] Write failing tests for registering multiple external systems under one business line.
- [ ] Implement `ExternalAgentConnection`.
- [ ] Store adapter type, endpoint/config, capabilities, status.
- [ ] Ensure query defaults to one business line.
- [ ] Run focused tests.

### Task 3: External Adapter Contract

**Files:**
- Create: `loop_harness/external_agents/adapter.py`
- Test: `tests/test_v77_agent_config_external_adapters.py`

- [ ] Write failing tests for adapter method contracts: run_task, run_shadow, get_metrics, get_trace.
- [ ] Implement base protocol and a deterministic dummy external adapter.
- [ ] Keep apply_change and rollback declared but optional / unsupported by default.
- [ ] Run focused tests.

### Task 4: API And UI Configuration Surface

**Files:**
- Modify: `loop_harness/api.py`
- Modify: `web/src/types/api.ts`
- Modify: `web/src/api/client.ts`
- Create: `web/src/features/agents/AgentConfigPage.tsx`
- Create: `web/src/features/external-agents/ExternalAgentPage.tsx`
- Modify: `web/src/app/App.tsx`
- Modify: `web/src/layout/Layout.tsx`

- [ ] Add API tests for agent config CRUD and external connection listing.
- [ ] Add React pages for Agent Config and External Agents.
- [ ] Keep UI as configuration forms, not code editor.
- [ ] Ensure Hermes is not required for config changes.

### Task 5: User Profile And Suggested Notes

**Files:**
- Create: `user/USER_PROFILE.md`
- Create: `user/SUGGESTED_PROFILE_NOTES.md`
- Create: `loop_harness/user_profile/__init__.py`
- Create: `loop_harness/user_profile/models.py`
- Create: `loop_harness/user_profile/store.py`
- Test: `tests/test_v77_user_profile.py`

- [ ] Write failing tests proving `USER_PROFILE.md` can be read and versioned.
- [ ] Write failing tests proving Hermes suggested notes are not treated as formal preferences.
- [ ] Implement `UserProfileStore` with read, save, diff, and version history.
- [ ] Ensure save requires `created_by="human"` and a reason/comment.
- [ ] Record every formal profile save in `DecisionLog`.
- [ ] Run focused tests.

### Task 6: User Profile UI

**Files:**
- Modify: `loop_harness/api.py`
- Modify: `web/src/types/api.ts`
- Modify: `web/src/api/client.ts`
- Create: `web/src/features/settings/UserProfilePage.tsx`
- Modify: `web/src/app/App.tsx`
- Modify: `web/src/layout/Layout.tsx`
- Test: `web/tests/e2e/console.spec.ts`

- [ ] Add API tests for reading profile, saving profile, reading suggested notes, and generating suggested notes placeholder.
- [ ] Add Settings -> User Profile page.
- [ ] Show formal profile on the left and Hermes suggested notes on the right.
- [ ] Provide `[Edit]`, `[Preview Diff]`, `[Save]`, `[Copy Suggested Text]`, `[Dismiss]`.
- [ ] Do not provide `[Apply Hermes Suggestion]`.
- [ ] Run frontend lint/build checks.

### Task 7: Agent Context Injection

**Files:**
- Modify: `loop_harness/agent_config/models.py`
- Create: `loop_harness/agent_config/context.py`
- Test: `tests/test_v77_user_profile.py`

- [ ] Write failing tests proving Agent context includes `USER_PROFILE.md`.
- [ ] Write failing tests proving Agent context excludes `SUGGESTED_PROFILE_NOTES.md`.
- [ ] Implement context builder with precedence: global profile -> business line profile -> scenario config.
- [ ] Ensure lower-level preferences cannot override upper-level `Forbidden` rules.

### Task 8: Verification

**Commands:**
- `python -m unittest tests/test_v77_agent_config_external_adapters.py -v`
- `python -m unittest tests/test_v77_user_profile.py -v`
- `python -m unittest discover -s tests -v`
- `python -m ruff check loop_harness tests scripts examples`
- `python -m mypy loop_harness --show-error-codes --no-incremental`
- `npm run lint`
- `npm run format:check`
- `npm run build`

- [ ] Run all commands.
- [ ] Fix failures before moving to V7.8.
