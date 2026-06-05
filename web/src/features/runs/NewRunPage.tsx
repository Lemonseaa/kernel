import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";
import { listAdapters, listScenarios, triggerRun } from "../../api/client";
import { Card } from "../../components/Card";
import { JsonBlock } from "../../components/JsonBlock";
import { PageHeader } from "../../components/PageHeader";

export function NewRunPage() {
  const queryClient = useQueryClient();
  const scenarios = useQuery({ queryKey: ["scenarios"], queryFn: listScenarios });
  const adapters = useQuery({ queryKey: ["adapters"], queryFn: listAdapters });
  const [scenarioId, setScenarioId] = useState("");
  const [task, setTask] = useState("analyze_signal");
  const [context, setContext] = useState('{"symbol":"AAPL"}');
  const run = useMutation({
    mutationFn: () =>
      triggerRun({ scenario_id: scenarioId, task, context: JSON.parse(context) as Record<string, unknown> }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["runs"] });
      await queryClient.invalidateQueries({ queryKey: ["snapshot"] });
    }
  });

  const scenario = scenarios.data?.find((item) => item.id === scenarioId);
  const adapter = adapters.data?.find((item) => item.name === scenario?.adapter_type);

  return (
    <>
      <PageHeader
        title="Trigger Run"
        description="Run an adapter manually and capture logs, metrics, and value summary."
      />
      <div className="grid gap-5 xl:grid-cols-[1fr_420px]">
        <Card title="Run Input">
          <div className="space-y-4">
            <label className="block text-sm text-muted">
              Scenario
              <select
                value={scenarioId}
                onChange={(event) => setScenarioId(event.target.value)}
                className="mt-2 h-10 w-full rounded-md border border-border px-3 text-sm text-ink outline-none focus:border-accent"
              >
                <option value="">Select scenario</option>
                {scenarios.data?.map((scenarioItem) => (
                  <option key={scenarioItem.id} value={scenarioItem.id}>
                    {scenarioItem.name} ({scenarioItem.adapter_type})
                  </option>
                ))}
              </select>
            </label>
            <label className="block text-sm text-muted">
              Task
              <input
                value={task}
                onChange={(event) => setTask(event.target.value)}
                className="mt-2 h-10 w-full rounded-md border border-border px-3 text-sm text-ink outline-none focus:border-accent"
              />
            </label>
            <label className="block text-sm text-muted">
              Context JSON
              <textarea
                value={context}
                onChange={(event) => setContext(event.target.value)}
                className="mt-2 min-h-40 w-full rounded-md border border-border px-3 py-2 font-mono text-sm text-ink outline-none focus:border-accent"
              />
            </label>
            <button
              className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
              disabled={!scenarioId || !task || run.isPending}
              onClick={() => run.mutate()}
            >
              Run Adapter
            </button>
          </div>
        </Card>
        <Card title="Adapter Contract">
          <JsonBlock value={adapter ?? { message: "Select a scenario to inspect adapter capabilities." }} />
        </Card>
      </div>
      {run.data ? (
        <div className="mt-5">
          <Card
            title="Run Result"
            action={
              <Link className="text-sm text-accent" to={`/runs/${run.data.run_id}`}>
                Open detail
              </Link>
            }
          >
            <JsonBlock value={run.data} />
          </Card>
        </div>
      ) : null}
      {run.error ? (
        <p className="mt-4 text-sm text-red-700">Run failed. Check scenario, adapter, and context JSON.</p>
      ) : null}
    </>
  );
}
