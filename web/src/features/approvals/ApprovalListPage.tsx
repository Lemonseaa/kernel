import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { listApprovals } from "../../api/client";
import { Card } from "../../components/Card";
import { DataTable } from "../../components/DataTable";
import { EmptyState } from "../../components/EmptyState";
import { PageHeader } from "../../components/PageHeader";
import { StatusBadge } from "../../components/StatusBadge";
import { formatDate } from "../../lib/format";
import { useUiStore } from "../../stores/uiStore";
import type { ApprovalItem } from "../../types/api";

export function ApprovalListPage() {
  const selectedScenarioId = useUiStore((state) => state.selectedScenarioId);
  const approvals = useQuery({
    queryKey: ["approvals", selectedScenarioId],
    queryFn: () => listApprovals(selectedScenarioId || undefined)
  });

  return (
    <>
      <PageHeader title="Approval Inbox" description="Human action queue for proposals, recommendations, and parameter suggestions." />
      <Card title="Pending Items">
        {approvals.data?.length ? (
          <DataTable<ApprovalItem>
            rows={approvals.data}
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
              { key: "type", header: "Type", render: (row) => row.item_type },
              { key: "status", header: "Status", render: (row) => <StatusBadge value={row.status} /> },
              { key: "created", header: "Created", render: (row) => formatDate(row.created_at) }
            ]}
          />
        ) : (
          <EmptyState title="No approval items" body="Nothing is waiting for human action." />
        )}
      </Card>
    </>
  );
}
