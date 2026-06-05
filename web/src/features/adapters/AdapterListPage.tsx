import { useQuery } from "@tanstack/react-query";
import { listAdapters } from "../../api/client";
import { Card } from "../../components/Card";
import { DataTable } from "../../components/DataTable";
import { EmptyState } from "../../components/EmptyState";
import { JsonBlock } from "../../components/JsonBlock";
import { PageHeader } from "../../components/PageHeader";
import type { AdapterDescription } from "../../types/api";

export function AdapterListPage() {
  const adapters = useQuery({ queryKey: ["adapters"], queryFn: listAdapters });

  return (
    <>
      <PageHeader title="Adapters" description="Registered adapter contracts and declared capabilities." />
      <Card title="Registered Adapters">
        {adapters.data?.length ? (
          <DataTable<AdapterDescription>
            rows={adapters.data}
            columns={[
              {
                key: "name",
                header: "Name",
                render: (row) => <span className="font-medium text-ink">{row.name}</span>
              },
              {
                key: "tasks",
                header: "Task Types",
                render: (row) => row.supported_task_types.join(", ") || "-"
              },
              {
                key: "capabilities",
                header: "Capabilities",
                render: (row) => <JsonBlock value={row.capabilities} />
              }
            ]}
          />
        ) : (
          <EmptyState
            title="No adapters"
            body="Register an adapter in the backend before running scenarios."
          />
        )}
      </Card>
    </>
  );
}
