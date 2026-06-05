import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import {
  getApiErrorMessage,
  getAutonomyQueueStatus,
  listAutonomyActions,
  listScenarios,
  pauseAutonomyQueue,
  processAutonomyAction,
  resumeAutonomyQueue
} from "../../api/client";
import { Card } from "../../components/Card";
import { DataTable } from "../../components/DataTable";
import { EmptyState } from "../../components/EmptyState";
import { JsonBlock } from "../../components/JsonBlock";
import { PageHeader } from "../../components/PageHeader";
import { StatusBadge } from "../../components/StatusBadge";
import { formatDate, shortId } from "../../lib/format";
import type { AutonomyAction } from "../../types/api";

export function AutonomyPage() {
  const queryClient = useQueryClient();
  const [scenarioId, setScenarioId] = useState("");
  const [lastResult, setLastResult] = useState<unknown>(null);
  const scenarios = useQuery({ queryKey: ["scenarios"], queryFn: listScenarios });
  const status = useQuery({ queryKey: ["autonomy", "status"], queryFn: getAutonomyQueueStatus });
  const actions = useQuery({
    queryKey: ["autonomy", "actions", scenarioId],
    queryFn: () => listAutonomyActions(scenarioId || undefined)
  });
  const refresh = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["autonomy", "status"] }),
      queryClient.invalidateQueries({ queryKey: ["autonomy", "actions"] })
    ]);
  };
  const pause = useMutation({
    mutationFn: pauseAutonomyQueue,
    onSuccess: async (result) => {
      setLastResult(result);
      await refresh();
    }
  });
  const resume = useMutation({
    mutationFn: resumeAutonomyQueue,
    onSuccess: async (result) => {
      setLastResult(result);
      await refresh();
    }
  });
  const process = useMutation({
    mutationFn: processAutonomyAction,
    onSuccess: async (result) => {
      setLastResult(result);
      await refresh();
    }
  });
  const error = pause.error ?? resume.error ?? process.error ?? actions.error ?? status.error;

  return (
    <>
      <PageHeader
        title="Autonomy"
        description="Operator controls for low-risk queued actions. Processing is audit-only until a safe apply backend is installed."
      />
      <div className="mb-5 grid gap-5 xl:grid-cols-[360px_1fr]">
        <Card title="Queue Status">
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <StatusBadge value={status.data?.paused ? "paused" : "running"} />
              <span className="text-sm text-muted">
                pending {status.data?.pending_count ?? 0} / running {status.data?.running_count ?? 0}
              </span>
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                className="rounded-md border border-border px-3 py-2 text-sm text-ink hover:bg-slate-50 disabled:opacity-50"
                disabled={pause.isPending || status.data?.paused}
                onClick={() => pause.mutate()}
              >
                Pause
              </button>
              <button
                className="rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
                disabled={resume.isPending || !status.data?.paused}
                onClick={() => resume.mutate()}
              >
                Resume
              </button>
            </div>
            {error ? <p className="text-sm text-red-700">{getApiErrorMessage(error)}</p> : null}
          </div>
        </Card>
        <Card title="Last Queue Result">
          {lastResult ? (
            <JsonBlock value={lastResult} />
          ) : (
            <p className="text-sm text-muted">No autonomy action processed in this session.</p>
          )}
        </Card>
      </div>
      <Card title="Action Queue">
        <div className="mb-4 max-w-sm">
          <label className="block text-sm text-muted">
            Scenario filter
            <select
              value={scenarioId}
              onChange={(event) => setScenarioId(event.target.value)}
              className="mt-2 h-10 w-full rounded-md border border-border px-3 text-sm text-ink outline-none focus:border-accent"
            >
              <option value="">All scenarios</option>
              {scenarios.data?.map((scenario) => (
                <option key={scenario.id} value={scenario.id}>
                  {scenario.name}
                </option>
              ))}
            </select>
          </label>
        </div>
        {actions.data?.length ? (
          <DataTable<AutonomyAction>
            rows={actions.data}
            columns={[
              { key: "id", header: "ID", render: (row) => shortId(row.id) },
              { key: "scenario", header: "Scenario", render: (row) => row.scenario_id },
              { key: "proposal", header: "Proposal", render: (row) => shortId(row.proposal_id) },
              { key: "type", header: "Type", render: (row) => row.action_type },
              { key: "checkpoint", header: "Checkpoint", render: (row) => shortId(row.checkpoint_id) },
              { key: "status", header: "Status", render: (row) => <StatusBadge value={row.status} /> },
              { key: "reason", header: "Reason", render: (row) => row.reason },
              { key: "created", header: "Created", render: (row) => formatDate(row.created_at) },
              {
                key: "action",
                header: "",
                render: (row) => (
                  <button
                    className="rounded-md border border-border px-3 py-1.5 text-xs font-medium text-ink hover:bg-slate-50 disabled:opacity-50"
                    disabled={row.status !== "pending" || process.isPending || status.data?.paused}
                    onClick={() => process.mutate(row.id)}
                  >
                    Process
                  </button>
                )
              }
            ]}
          />
        ) : (
          <EmptyState
            title="No autonomy actions"
            body="Eligible low-risk actions will appear here before processing."
          />
        )}
      </Card>
    </>
  );
}
