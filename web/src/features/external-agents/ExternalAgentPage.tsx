import { useQuery } from "@tanstack/react-query";
import { listExternalAgents } from "../../api/client";
import { Card } from "../../components/Card";
import { DataTable } from "../../components/DataTable";
import { EmptyState } from "../../components/EmptyState";
import { JsonBlock } from "../../components/JsonBlock";
import { PageHeader } from "../../components/PageHeader";
import type { ExternalAgentConnection } from "../../types/api";

export function ExternalAgentPage() {
  const agents = useQuery({ queryKey: ["external-agents"], queryFn: listExternalAgents });

  return (
    <>
      <PageHeader title="External Agents" description="Business-line bound external Agent connections and capabilities." />
      <Card title="Connections">
        {agents.data?.length ? (
          <DataTable<ExternalAgentConnection>
            rows={agents.data}
            columns={[
              { key: "name", header: "Name", render: (row) => row.name },
              { key: "adapter", header: "Adapter", render: (row) => row.adapter_type },
              { key: "scenario", header: "Scenario", render: (row) => row.scenario_id },
              { key: "capabilities", header: "Capabilities", render: (row) => <JsonBlock value={row.capabilities} /> }
            ]}
          />
        ) : (
          <EmptyState title="No external agents" body="Attach external Agent systems through the backend API." />
        )}
      </Card>
    </>
  );
}
