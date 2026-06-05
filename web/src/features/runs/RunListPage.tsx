import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { listRuns } from "../../api/client";
import { Card } from "../../components/Card";
import { DataTable } from "../../components/DataTable";
import { EmptyState } from "../../components/EmptyState";
import { PageHeader } from "../../components/PageHeader";
import { StatusBadge } from "../../components/StatusBadge";
import { formatDate, shortId } from "../../lib/format";
import { useUiStore } from "../../stores/uiStore";
import type { RunSummary } from "../../types/api";

export function RunListPage() {
  const selectedScenarioId = useUiStore((state) => state.selectedScenarioId);
  const runs = useQuery({
    queryKey: ["runs", selectedScenarioId],
    queryFn: () => listRuns(selectedScenarioId || undefined)
  });

  return (
    <>
      <PageHeader title="Run History" description="Past adapter runs with metrics, summaries, and status." />
      <Card title="Runs" action={<Link className="text-sm text-accent" to="/runs/new">Trigger run</Link>}>
        {runs.data?.length ? (
          <DataTable<RunSummary>
            rows={runs.data}
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
              { key: "summary", header: "Value", render: (row) => row.value_summary || row.failed_summary || "-" },
              { key: "created", header: "Created", render: (row) => formatDate(row.created_at) }
            ]}
          />
        ) : (
          <EmptyState title="No runs yet" body="Trigger a run from the console to collect evidence." />
        )}
      </Card>
    </>
  );
}
