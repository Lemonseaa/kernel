import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { getApiErrorMessage, getSnapshot } from "../../api/client";
import { Card } from "../../components/Card";
import { DataTable } from "../../components/DataTable";
import { EmptyState } from "../../components/EmptyState";
import { MetricGrid } from "../../components/MetricGrid";
import { PageHeader } from "../../components/PageHeader";
import { StatusBadge } from "../../components/StatusBadge";
import { formatDate, shortId } from "../../lib/format";
import { useUiStore } from "../../stores/uiStore";
import type { ApprovalItem, RunSummary, ScenarioSummary } from "../../types/api";

export function DashboardPage() {
  const selectedScenarioId = useUiStore((state) => state.selectedScenarioId);
  const snapshot = useQuery({
    queryKey: ["snapshot", selectedScenarioId],
    queryFn: () => getSnapshot(selectedScenarioId || undefined)
  });

  const data = snapshot.data;

  return (
    <>
      <PageHeader
        title="Dashboard"
        description="Operator view for scenario health, recent runs, approvals, and system activity."
      />
      {snapshot.isError ? (
        <EmptyState title="API unavailable" body={getApiErrorMessage(snapshot.error)} />
      ) : null}
      <MetricGrid
        metrics={[
          {
            label: "Scenarios",
            value: data?.scenario_count ?? "-",
            caption: `${data?.active_scenario_count ?? 0} active`
          },
          {
            label: "Recent runs",
            value: data?.recent_run_count ?? "-",
            caption: `${data?.failed_run_count ?? 0} failed`
          },
          {
            label: "Pending approvals",
            value: data?.pending_approval_count ?? "-",
            caption: "Human action queue"
          },
          {
            label: "Scope",
            value: data?.scope.scenario_id ?? "all",
            caption: data?.operator_summary ?? "Waiting for API"
          }
        ]}
      />

      <div className="mt-5 grid gap-5 xl:grid-cols-2">
        <Card title="Scenarios">
          {data?.scenarios.length ? (
            <DataTable<ScenarioSummary>
              rows={data.scenarios}
              columns={[
                {
                  key: "name",
                  header: "Name",
                  render: (row) => <span className="font-medium text-ink">{row.name}</span>
                },
                { key: "adapter", header: "Adapter", render: (row) => row.adapter_type },
                { key: "status", header: "Status", render: (row) => <StatusBadge value={row.status} /> }
              ]}
            />
          ) : (
            <EmptyState title="No scenarios" body="Create or load a scenario before running agents." />
          )}
        </Card>

        <Card
          title="Pending Approvals"
          action={
            <Link className="text-sm text-accent" to="/approvals">
              View all
            </Link>
          }
        >
          {data?.pending_items.length ? (
            <DataTable<ApprovalItem>
              rows={data.pending_items}
              columns={[
                {
                  key: "title",
                  header: "Item",
                  render: (row) => (
                    <Link className="font-medium text-accent" to={`/approvals/${row.source_id}`}>
                      {row.title}
                    </Link>
                  )
                },
                { key: "scenario", header: "Scenario", render: (row) => row.scenario_id },
                { key: "status", header: "Status", render: (row) => <StatusBadge value={row.status} /> }
              ]}
            />
          ) : (
            <EmptyState title="No pending approvals" body="The human queue is currently clear." />
          )}
        </Card>
      </div>

      <div className="mt-5">
        <Card
          title="Recent Runs"
          action={
            <Link className="text-sm text-accent" to="/runs">
              View history
            </Link>
          }
        >
          {data?.latest_runs.length ? (
            <DataTable<RunSummary>
              rows={data.latest_runs}
              columns={[
                {
                  key: "run",
                  header: "Run",
                  render: (row) => (
                    <Link className="font-medium text-accent" to={`/runs/${row.run_id}`}>
                      {shortId(row.run_id)}
                    </Link>
                  )
                },
                { key: "scenario", header: "Scenario", render: (row) => row.scenario_id },
                { key: "task", header: "Task", render: (row) => row.task },
                { key: "status", header: "Status", render: (row) => <StatusBadge value={row.status} /> },
                { key: "time", header: "Created", render: (row) => formatDate(row.created_at) }
              ]}
            />
          ) : (
            <EmptyState title="No runs" body="Trigger a run to populate this table." />
          )}
        </Card>
      </div>
    </>
  );
}
