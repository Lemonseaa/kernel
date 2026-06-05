import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { listScenarios, listShadows, triggerShadow } from "../../api/client";
import { Card } from "../../components/Card";
import { DataTable } from "../../components/DataTable";
import { EmptyState } from "../../components/EmptyState";
import { JsonBlock } from "../../components/JsonBlock";
import { PageHeader } from "../../components/PageHeader";
import { StatusBadge } from "../../components/StatusBadge";
import { formatDate, shortId } from "../../lib/format";
import type { ShadowResult } from "../../types/api";

export function ShadowListPage() {
  const queryClient = useQueryClient();
  const [scenarioId, setScenarioId] = useState("");
  const [proposalId, setProposalId] = useState("");
  const [context, setContext] = useState('{"symbol":"SPY"}');
  const scenarios = useQuery({ queryKey: ["scenarios"], queryFn: listScenarios });
  const shadows = useQuery({
    queryKey: ["shadows", scenarioId],
    queryFn: () => listShadows(scenarioId || undefined)
  });
  const runShadow = useMutation({
    mutationFn: () =>
      triggerShadow({
        proposal_id: proposalId,
        task: "analyze_signal",
        context: JSON.parse(context) as Record<string, unknown>,
        config: { run_kind: "synthetic" }
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["shadows"] });
    }
  });

  return (
    <>
      <PageHeader
        title="Shadow Runs"
        description="Run candidate changes without changing deployed prompts."
      />
      <div className="mb-5 grid gap-5 xl:grid-cols-[420px_1fr]">
        <Card title="Trigger Shadow">
          <div className="space-y-4">
            <label className="block text-sm text-muted">
              Proposal ID
              <input
                value={proposalId}
                onChange={(event) => setProposalId(event.target.value)}
                className="mt-2 h-10 w-full rounded-md border border-border px-3 text-sm text-ink outline-none focus:border-accent"
                placeholder="Prompt proposal id"
              />
            </label>
            <label className="block text-sm text-muted">
              Context JSON
              <textarea
                value={context}
                onChange={(event) => setContext(event.target.value)}
                className="mt-2 min-h-28 w-full rounded-md border border-border px-3 py-2 font-mono text-sm text-ink outline-none focus:border-accent"
              />
            </label>
            <button
              className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
              disabled={!proposalId.trim() || runShadow.isPending}
              onClick={() => runShadow.mutate()}
            >
              Run Shadow
            </button>
          </div>
        </Card>
        <Card title="Latest Shadow Result">
          {runShadow.data ? (
            <JsonBlock value={runShadow.data} />
          ) : (
            <p className="text-sm text-muted">No shadow run triggered in this session.</p>
          )}
        </Card>
      </div>
      <Card title="Shadow History">
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
        {shadows.data?.length ? (
          <DataTable<ShadowResult>
            rows={shadows.data}
            columns={[
              { key: "id", header: "ID", render: (row) => shortId(row.id) },
              { key: "scenario", header: "Scenario", render: (row) => row.scenario_id },
              { key: "proposal", header: "Proposal", render: (row) => shortId(row.proposal_id) },
              { key: "status", header: "Status", render: (row) => <StatusBadge value={row.status} /> },
              { key: "passed", header: "Passed", render: (row) => String(row.passed) },
              { key: "created", header: "Created", render: (row) => formatDate(row.created_at) }
            ]}
          />
        ) : (
          <EmptyState title="No shadow results" body="Run a shadow test from an approval proposal first." />
        )}
      </Card>
    </>
  );
}
