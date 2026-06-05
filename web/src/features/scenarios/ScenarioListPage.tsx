import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { archiveScenario, listScenarios } from "../../api/client";
import { Card } from "../../components/Card";
import { DataTable } from "../../components/DataTable";
import { EmptyState } from "../../components/EmptyState";
import { JsonBlock } from "../../components/JsonBlock";
import { PageHeader } from "../../components/PageHeader";
import { StatusBadge } from "../../components/StatusBadge";
import { useUiStore } from "../../stores/uiStore";
import type { Scenario } from "../../types/api";

export function ScenarioListPage() {
  const queryClient = useQueryClient();
  const selectedScenarioId = useUiStore((state) => state.selectedScenarioId);
  const setSelectedScenarioId = useUiStore((state) => state.setSelectedScenarioId);
  const scenarios = useQuery({ queryKey: ["scenarios"], queryFn: listScenarios });
  const archive = useMutation({
    mutationFn: (id: string) => archiveScenario(id, "Archived from Web Console."),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["scenarios"] })
  });
  const selected = scenarios.data?.find((scenario) => scenario.id === selectedScenarioId);

  return (
    <>
      <PageHeader title="Scenarios" description="Scenario scope controls isolation for runs, proposals, prompts, and reports." />
      <div className="grid gap-5 xl:grid-cols-[1fr_420px]">
        <Card title="Scenario List">
          {scenarios.data?.length ? (
            <DataTable<Scenario>
              rows={scenarios.data}
              columns={[
                {
                  key: "name",
                  header: "Name",
                  render: (row) => (
                    <button className="font-medium text-accent" onClick={() => setSelectedScenarioId(row.id)}>
                      {row.name}
                    </button>
                  )
                },
                { key: "adapter", header: "Adapter", render: (row) => row.adapter_type },
                { key: "status", header: "Status", render: (row) => <StatusBadge value={row.status} /> },
                {
                  key: "scope",
                  header: "Scope",
                  render: (row) => (
                    <button
                      className="rounded-md border border-border px-3 py-1.5 text-xs font-medium text-ink hover:bg-slate-50"
                      onClick={() => setSelectedScenarioId(row.id)}
                    >
                      Use scope
                    </button>
                  )
                },
                {
                  key: "archive",
                  header: "Archive",
                  render: (row) => (
                    <button
                      className="rounded-md border border-border px-3 py-1.5 text-xs font-medium text-ink hover:bg-slate-50 disabled:opacity-50"
                      disabled={archive.isPending || row.status === "archived"}
                      onClick={() => archive.mutate(row.id)}
                    >
                      Archive
                    </button>
                  )
                }
              ]}
            />
          ) : (
            <EmptyState title="No scenarios" body="Scenarios are created through backend setup or CLI in this phase." />
          )}
        </Card>
        <Card title="Selected Scenario">
          <JsonBlock value={selected ?? { selectedScenarioId: selectedScenarioId || "all" }} />
        </Card>
      </div>
    </>
  );
}
