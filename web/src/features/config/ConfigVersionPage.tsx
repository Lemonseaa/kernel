import { useQuery } from "@tanstack/react-query";
import { listConfigVersions } from "../../api/client";
import { Card } from "../../components/Card";
import { DataTable } from "../../components/DataTable";
import { EmptyState } from "../../components/EmptyState";
import { JsonBlock } from "../../components/JsonBlock";
import { PageHeader } from "../../components/PageHeader";
import type { ConfigVersion } from "../../types/api";

export function ConfigVersionPage() {
  const versions = useQuery({ queryKey: ["config-versions"], queryFn: listConfigVersions });

  return (
    <>
      <PageHeader title="Config Versions" description="Locked snapshots and branch-ready configuration history." />
      <Card title="Versions">
        {versions.data?.length ? (
          <DataTable<ConfigVersion>
            rows={versions.data}
            columns={[
              { key: "id", header: "Version", render: (row) => row.id.slice(0, 8) },
              { key: "scenario", header: "Scenario", render: (row) => row.scenario_id },
              { key: "locked", header: "Locked", render: (row) => (row.locked ? "yes" : "no") },
              { key: "reason", header: "Reason", render: (row) => row.reason },
              { key: "config", header: "Config", render: (row) => <JsonBlock value={row.config} /> }
            ]}
          />
        ) : (
          <EmptyState title="No config versions" body="Save and lock good configurations before branching." />
        )}
      </Card>
    </>
  );
}
