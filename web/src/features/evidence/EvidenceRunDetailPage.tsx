import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { useState } from "react";
import { getEvidenceBaseline, getEvidenceRun, setEvidenceBaseline } from "../../api/client";
import { Card } from "../../components/Card";
import { MetricGrid } from "../../components/MetricGrid";
import { PageHeader } from "../../components/PageHeader";
import { StatusBadge } from "../../components/StatusBadge";
import { EvidenceQualityPanel } from "./EvidenceQualityPanel";
import { NodeInspector } from "./NodeInspector";
import { WorkflowMap } from "./WorkflowMap";

export function EvidenceRunDetailPage() {
  const { runId = "" } = useParams();
  const [selectedNodeId, setSelectedNodeId] = useState("");
  const queryClient = useQueryClient();
  const evidenceRun = useQuery({
    queryKey: ["evidence-run", runId],
    queryFn: () => getEvidenceRun(runId),
    enabled: Boolean(runId)
  });
  const stored = evidenceRun.data;
  const workflowId = stored?.run.workflow_id || "";
  const baseline = useQuery({
    queryKey: ["evidence-baseline", workflowId],
    queryFn: () => getEvidenceBaseline(workflowId),
    enabled: Boolean(workflowId),
    retry: false
  });
  const setBaseline = useMutation({
    mutationFn: () => setEvidenceBaseline(workflowId, runId, "Pinned from Evidence Run Detail."),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["evidence-baseline", workflowId] });
    }
  });
  const isActiveBaseline = baseline.data?.baseline_run_id === runId;
  const activeNodeId =
    stored && stored.visualization.nodes.some((node) => node.id === selectedNodeId)
      ? selectedNodeId
      : stored?.visualization.run_path[0] || stored?.visualization.nodes[0]?.id || "";

  return (
    <>
      <PageHeader
        title="Evidence Run Detail"
        description="Node-level evidence, workflow path, report summary, and coverage for one external workflow run."
      />

      <div className="mb-5">
        <Link className="rounded-md border border-border px-3 py-2 text-sm font-medium text-ink" to="/evidence">
          Back to evidence
        </Link>
      </div>

      {stored ? (
        <>
          <MetricGrid
            metrics={[
              { label: "Run", value: stored.run.run_id },
              { label: "Workflow", value: stored.run.workflow_id },
              { label: "Trace Coverage", value: `${Math.round(stored.visualization.trace_coverage * 100)}%` },
              { label: "Metric Coverage", value: `${Math.round(stored.visualization.metric_coverage * 100)}%` }
            ]}
          />

          <div className="mt-5 grid gap-5 xl:grid-cols-[1fr_440px]">
            <Card
              title="Workflow Visualization"
              action={
                <div className="flex flex-wrap items-center gap-2">
                  {isActiveBaseline ? <StatusBadge value="Active baseline" /> : null}
                  <StatusBadge value={stored.report.recommendation} />
                </div>
              }
            >
              <WorkflowMap
                visualization={stored.visualization}
                selectedNodeId={activeNodeId}
                onSelectNode={setSelectedNodeId}
              />
            </Card>

            <Card title="Run Report">
              <p className="text-sm text-ink">{stored.report.summary}</p>
              <div className="mt-3 text-xs text-muted">
                Kind: {stored.run.run_kind} / Black boxes: {stored.visualization.black_box_node_ids.length}
              </div>
              <button
                className="mt-4 rounded-md bg-accent px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-border disabled:text-muted"
                disabled={setBaseline.isPending || isActiveBaseline}
                onClick={() => setBaseline.mutate()}
              >
                {isActiveBaseline ? "Active baseline" : "Set as baseline"}
              </button>
            </Card>
          </div>

          <div className="mt-5">
            <div className="grid gap-5 xl:grid-cols-[1fr_440px]">
              <Card title="Node Evidence">
                <NodeInspector visualization={stored.visualization} nodeId={activeNodeId} />
              </Card>
              <Card title="Evidence Quality">
                <EvidenceQualityPanel report={stored.report} />
              </Card>
            </div>
          </div>
        </>
      ) : (
        <Card title="Evidence run unavailable">
          <p className="text-sm text-muted">
            {evidenceRun.isError ? "This evidence run could not be loaded." : "Loading evidence run..."}
          </p>
        </Card>
      )}
    </>
  );
}
