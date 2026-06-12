# Evidence Console Comparison Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Evidence UI prove optimization impact with realistic mocked data, not just render an empty shell.

**Architecture:** Keep learning and comparison logic in the backend Evidence API. The web console only calls existing endpoints, renders baseline/candidate choices, and visualizes metric deltas. E2E tests intercept API responses so the UI is verified with real-shaped data without requiring a backend server.

**Tech Stack:** React, TanStack Query, Axios, Playwright, TypeScript.

---

### Task 1: Type the Comparison Payload

**Files:**
- Modify: `web/src/types/api.ts`
- Modify: `web/src/features/evidence/EvidencePage.tsx`

- [ ] Replace loose `Record<string, unknown>` comparison typing with a structured `ComparisonResult` type.
- [ ] Update EvidencePage helper functions to read typed metric diff fields.

### Task 2: Add Realistic Evidence E2E Fixtures

**Files:**
- Modify: `web/tests/e2e/console.spec.ts`

- [ ] Add two stored evidence runs with workflow nodes, trace coverage, metric coverage, reports, and business/system/data quality metrics.
- [ ] Add a comparison report containing business, system, and data quality metric deltas.

### Task 3: Mock Evidence API Routes in Playwright

**Files:**
- Modify: `web/tests/e2e/console.spec.ts`

- [ ] Intercept `GET /api/evidence/runs`.
- [ ] Intercept `POST /api/evidence/compare`.
- [ ] Keep the dashboard route tolerant of missing backend.

### Task 4: Verify Interactive Comparison Behavior

**Files:**
- Modify: `web/tests/e2e/console.spec.ts`

- [ ] Assert the Evidence page renders two real runs.
- [ ] Select baseline and candidate.
- [ ] Click Compare.
- [ ] Assert recommendation, summary, and metric delta values are visible.

### Task 5: Update Documentation and Run Verification

**Files:**
- Modify: `docs/core_innovation/impact_console.md`

- [ ] Document that the Evidence console uses baseline/candidate comparison and metric delta visualization.
- [ ] Run frontend lint/build/e2e.
- [ ] Run backend unit tests, ruff, mypy, and final acceptance.
