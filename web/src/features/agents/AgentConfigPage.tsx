import { useQuery } from "@tanstack/react-query";
import { listAgentConfigs } from "../../api/client";
import { Card } from "../../components/Card";
import { DataTable } from "../../components/DataTable";
import { EmptyState } from "../../components/EmptyState";
import { JsonBlock } from "../../components/JsonBlock";
import { PageHeader } from "../../components/PageHeader";
import type { AgentConfig } from "../../types/api";

export function AgentConfigPage() {
  const configs = useQuery({ queryKey: ["agent-configs"], queryFn: listAgentConfigs });

  return (
    <>
      <PageHeader title="Agent Config" description="Internal observer, proposer, validator, and safety monitor settings." />
      <Card title="Internal Agents">
        {configs.data?.length ? (
          <DataTable<AgentConfig>
            rows={configs.data}
            columns={[
              { key: "role", header: "Role", render: (row) => row.role },
              { key: "businessLine", header: "Business Line", render: (row) => row.business_line_id },
              { key: "model", header: "Model", render: (row) => row.model },
              {
                key: "controls",
                header: "Controls",
                render: (row) => <JsonBlock value={{ skills: row.skills, tools: row.tools, triggers: row.triggers }} />
              }
            ]}
          />
        ) : (
          <EmptyState title="No agent configs" body="Create role-scoped AgentConfig records from the backend API." />
        )}
      </Card>
    </>
  );
}
