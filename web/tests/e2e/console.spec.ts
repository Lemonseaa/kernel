import { expect, test } from "@playwright/test";

const evidenceRuns = [
  {
    run: {
      workflow_id: "quant-demo",
      run_id: "baseline-run-001",
      run_kind: "historical",
      metrics: { sharpe: 0.82, max_drawdown: 0.18, latency_ms: 120 },
      metadata: { strategy: "baseline" }
    },
    visualization: {
      workflow_id: "quant-demo",
      run_id: "baseline-run-001",
      nodes: [
        { id: "data", name: "Load data", type: "tool", metadata: { traced: true } },
        { id: "agent", name: "Strategy agent", type: "agent", metadata: { traced: true } }
      ],
      edges: [{ source: "data", target: "agent", type: "sequence", metadata: {} }],
      run_path: ["data", "agent"],
      total_nodes: 2,
      traced_node_ids: ["data", "agent"],
      metric_node_ids: ["agent"],
      black_box_node_ids: [],
      error_node_ids: [],
      trace_coverage: 1,
      metric_coverage: 0.5,
      node_costs: { agent: 0.12 },
      node_latencies_ms: { data: 20, agent: 100 }
    },
    report: {
      workflow_id: "quant-demo",
      run_id: "baseline-run-001",
      baseline_run_id: null,
      candidate_run_id: null,
      run_kind: "historical",
      trace_coverage: 1,
      metric_coverage: 0.5,
      black_box_node_ids: [],
      business_metrics: { sharpe: 0.82, max_drawdown: 0.18 },
      system_metrics: { latency_ms: 120 },
      data_quality_metrics: { sample_count: 120 },
      comparison: null,
      recommendation: "baseline_ready",
      summary: "Baseline strategy has enough trace coverage for comparison.",
      evidence: { quality: { status: "accepted", score: 1, reasons: [] } }
    }
  },
  {
    run: {
      workflow_id: "quant-demo",
      run_id: "candidate-run-002",
      run_kind: "historical",
      metrics: { sharpe: 1.08, max_drawdown: 0.13, latency_ms: 138 },
      metadata: { strategy: "candidate" }
    },
    visualization: {
      workflow_id: "quant-demo",
      run_id: "candidate-run-002",
      nodes: [
        { id: "data", name: "Load data", type: "tool", metadata: { traced: true } },
        { id: "agent", name: "Strategy agent", type: "agent", metadata: { traced: true } },
        { id: "risk", name: "Risk check", type: "tool", metadata: { traced: true } }
      ],
      edges: [
        { source: "data", target: "agent", type: "sequence", metadata: {} },
        { source: "agent", target: "risk", type: "sequence", metadata: {} }
      ],
      run_path: ["data", "agent", "risk"],
      total_nodes: 3,
      traced_node_ids: ["data", "agent", "risk"],
      metric_node_ids: ["agent", "risk"],
      black_box_node_ids: ["risk"],
      error_node_ids: [],
      trace_coverage: 0.67,
      metric_coverage: 0.67,
      node_costs: { agent: 0.15, risk: 0.02 },
      node_latencies_ms: { data: 20, agent: 110, risk: 8 }
    },
    report: {
      workflow_id: "quant-demo",
      run_id: "candidate-run-002",
      baseline_run_id: null,
      candidate_run_id: null,
      run_kind: "historical",
      trace_coverage: 0.67,
      metric_coverage: 0.67,
      black_box_node_ids: ["risk"],
      business_metrics: { sharpe: 1.08, max_drawdown: 0.13 },
      system_metrics: { latency_ms: 138 },
      data_quality_metrics: { sample_count: 120 },
      comparison: null,
      recommendation: "candidate_ready",
      summary: "Candidate strategy improves return profile with acceptable latency.",
      evidence: {
        quality: {
          status: "warning",
          score: 0.55,
          reasons: ["low_trace_coverage", "black_box_nodes_present"]
        }
      }
    }
  }
];

const comparisonReport = {
  workflow_id: "quant-demo",
  run_id: null,
  baseline_run_id: "baseline-run-001",
  candidate_run_id: "candidate-run-002",
  run_kind: "historical",
  trace_coverage: 0.67,
  metric_coverage: 0.67,
  black_box_node_ids: ["risk"],
  business_metrics: { sharpe: 1.08, max_drawdown: 0.13 },
  system_metrics: { latency_ms: 138 },
  data_quality_metrics: { sample_count: 120 },
  comparison: {
    metric_diffs: { sharpe: 0.26, max_drawdown: -0.05, latency_ms: 18, sample_count: 0 },
    business_metric_diffs: { sharpe: 0.26, max_drawdown: -0.05 },
    system_metric_diffs: { latency_ms: 18 },
    data_quality_metric_diffs: { sample_count: 0 },
    metric_evaluations: {},
    objective_score: 0.31,
    guardrail_violations: [],
    improved: true,
    summary: "Candidate improves Sharpe and lowers drawdown versus baseline.",
    run_kind: "historical",
    provenance: { source: "e2e-fixture" }
  },
  recommendation: "approve_candidate",
  summary: "Candidate improves Sharpe and lowers drawdown versus baseline.",
  evidence: {
    quality: {
      status: "warning",
      score: 0.55,
      reasons: ["low_trace_coverage", "black_box_nodes_present"]
    }
  }
};

let activeBaselineRunId = "";

test("renders the control console shell", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByText("Loop Harness").first()).toBeVisible();
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expect(page.getByLabel("API Token")).toBeVisible();
  await expect(page.getByRole("link", { name: "Approvals" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Evidence" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Runs" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Shadows" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Learning" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Autonomy" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Reports" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Config", exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: "Agent Config" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Profile" })).toBeVisible();
});

test("opens the evidence console page", async ({ page }) => {
  activeBaselineRunId = "";
  await page.route("**/api/evidence/runs", async (route) => {
    await route.fulfill({ json: evidenceRuns });
  });
  await page.route("**/api/evidence/runs/*", async (route) => {
    const runId = route.request().url().split("/").pop() ?? "";
    const stored = evidenceRuns.find((item) => item.run.run_id === runId);
    if (!stored) {
      await route.fulfill({ status: 404, json: { code: "evidence.run_not_found", message: "Missing", details: {} } });
      return;
    }
    await route.fulfill({ json: stored });
  });
  await page.route("**/api/evidence/compare", async (route) => {
    await route.fulfill({ json: comparisonReport });
  });
  await page.route("**/api/evidence/proposals", async (route) => {
    await route.fulfill({
      json: {
        id: "evidence-proposal-001",
        scenario_id: "quant",
        proposal_kind: "evidence",
        target_type: "deployment",
        target_id: "quant-demo:candidate-run-002",
        patch: {
          operation: "replace",
          before: { baseline_run_id: "baseline-run-001" },
          after: { candidate_run_id: "candidate-run-002" }
        },
        reason: "Candidate improves Sharpe and lowers drawdown versus baseline.",
        expected_metric: "objective_score",
        status: "proposed",
        created_at: "2026-06-11T00:00:00Z",
        updated_at: "2026-06-11T00:00:00Z",
        metadata: {}
      }
    });
  });
  await page.route("**/api/evidence/workflows/*/baseline", async (route) => {
    if (route.request().method() === "POST") {
      const body = route.request().postDataJSON() as { baseline_run_id: string; reason: string };
      activeBaselineRunId = body.baseline_run_id;
      await route.fulfill({
        json: {
          workflow_id: "quant-demo",
          baseline_run_id: activeBaselineRunId,
          reason: body.reason,
          created_at: "2026-06-11T00:00:00Z"
        }
      });
      return;
    }
    if (!activeBaselineRunId) {
      await route.fulfill({
        status: 404,
        json: { code: "evidence.baseline_not_found", message: "Missing", details: {} }
      });
      return;
    }
    await route.fulfill({
      json: {
        workflow_id: "quant-demo",
        baseline_run_id: activeBaselineRunId,
        reason: "Pinned from UI.",
        created_at: "2026-06-11T00:00:00Z"
      }
    });
  });

  await page.goto("/");

  await page.getByRole("link", { name: "Evidence" }).click();

  await expect(page).toHaveURL(/\/evidence$/);
  await expect(page.getByRole("heading", { name: "Evidence Runs" })).toBeVisible();
  await expect(page.getByText("Workflow Visualization")).toBeVisible();
  await expect(page.getByRole("button", { name: "baseline…" })).toBeVisible();
  await expect(page.getByRole("button", { name: "candidat…" })).toBeVisible();

  await page.getByRole("link", { name: "Open baseline…" }).click();

  await expect(page).toHaveURL(/\/evidence\/runs\/baseline-run-001$/);
  await expect(page.getByRole("heading", { name: "Evidence Run Detail" })).toBeVisible();
  await expect(page.getByText("Baseline strategy has enough trace coverage for comparison.")).toBeVisible();
  await expect(page.getByText("data → agent")).toBeVisible();

  await page.getByRole("button", { name: "Set as baseline" }).click();
  await expect(page.getByRole("button", { name: "Active baseline" })).toBeVisible();

  await page.getByRole("link", { name: "Back to evidence" }).click();
  await expect(page.getByText("Active baseline").first()).toBeVisible();
  await page.getByRole("button", { name: "candidat…" }).click();

  await page.getByRole("button", { name: "candidat…" }).click();

  await expect(page.getByText("Load data")).toBeVisible();
  await expect(page.getByText("Strategy agent")).toBeVisible();
  await expect(page.getByText("data → agent → risk")).toBeVisible();
  await expect(page.getByText("Traced").first()).toBeVisible();
  await expect(page.getByText("Metric").first()).toBeVisible();
  await expect(page.getByText("Black box").first()).toBeVisible();
  await expect(page.getByText("Error").first()).toBeVisible();
  await expect(page.getByText("Evidence Quality")).toBeVisible();
  await expect(page.getByText("warning")).toBeVisible();
  await expect(page.getByText("black_box_nodes_present")).toBeVisible();
  await expect(page.getByText("Baseline vs Candidate")).toBeVisible();
  await expect(page.getByLabel("Baseline run")).toBeVisible();
  await expect(page.getByLabel("Candidate run")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Metric Delta" })).toBeVisible();

  await page.getByRole("button", { name: "Strategy agent" }).click();

  const nodeEvidence = page.locator("section").filter({ has: page.getByRole("heading", { name: "Node Evidence" }) });
  await expect(nodeEvidence.getByRole("heading", { name: "Node Evidence" })).toBeVisible();
  await expect(nodeEvidence.getByText("Node id")).toBeVisible();
  await expect(nodeEvidence.getByText("agent", { exact: true }).first()).toBeVisible();
  await expect(nodeEvidence.getByText("Type")).toBeVisible();
  await expect(nodeEvidence.getByText("110 ms")).toBeVisible();
  await expect(nodeEvidence.getByText("$0.150")).toBeVisible();
  await expect(nodeEvidence.getByText("Metric captured")).toBeVisible();

  await page.getByRole("button", { name: "Risk check" }).click();
  await expect(nodeEvidence.getByText("Black-box node")).toBeVisible();

  await page.getByRole("button", { name: "Compare" }).click();

  await expect(page.getByText("approve_candidate")).toBeVisible();
  await expect(page.getByText("Candidate improves Sharpe and lowers drawdown versus baseline.")).toBeVisible();
  await expect(page.getByText("sharpe", { exact: true })).toBeVisible();
  await expect(page.getByText("business / +0.260")).toBeVisible();
  await expect(page.getByText("max_drawdown", { exact: true })).toBeVisible();
  await expect(page.getByText("system / +18.000")).toBeVisible();
  await page.getByRole("button", { name: "Create approval proposal" }).click();
  await expect(page.getByRole("link", { name: "Open approval evidence-proposal-001" })).toBeVisible();
  await expect(page.getByText("What to do next")).toBeVisible();
  await expect(page.getByText("Review candidate approval")).toBeVisible();
  await expect(page.getByText("Add trace coverage before trusting this workflow")).toBeVisible();
  await expect(page.getByText("Improve metric capture before optimization")).toBeVisible();
});
