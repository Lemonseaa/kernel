import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { getLatestReport, getProposalReport, getRunReport, listScenarios } from "../../api/client";
import { Card } from "../../components/Card";
import { PageHeader } from "../../components/PageHeader";

type ReportMode = "latest" | "run" | "proposal";

export function ReportsPage() {
  const scenarios = useQuery({ queryKey: ["scenarios"], queryFn: listScenarios });
  const [mode, setMode] = useState<ReportMode>("latest");
  const [scenarioId, setScenarioId] = useState("");
  const [targetId, setTargetId] = useState("");
  const report = useQuery({
    queryKey: ["report", mode, scenarioId, targetId],
    queryFn: () => {
      if (mode === "run") {
        return getRunReport(targetId);
      }
      if (mode === "proposal") {
        return getProposalReport(targetId);
      }
      return getLatestReport(scenarioId || undefined);
    },
    enabled: mode === "latest" || Boolean(targetId.trim())
  });

  return (
    <>
      <PageHeader title="Reports" description="Readable evidence reports for runs and proposals." />
      <div className="grid gap-5 xl:grid-cols-[360px_1fr]">
        <Card title="Report Query">
          <div className="space-y-4">
            <label className="block text-sm text-muted">
              Report type
              <select
                value={mode}
                onChange={(event) => setMode(event.target.value as ReportMode)}
                className="mt-2 h-10 w-full rounded-md border border-border px-3 text-sm text-ink outline-none focus:border-accent"
              >
                <option value="latest">Latest run</option>
                <option value="run">Run by ID</option>
                <option value="proposal">Proposal by ID</option>
              </select>
            </label>
            {mode === "latest" ? (
              <label className="block text-sm text-muted">
                Scenario scope
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
            ) : (
              <label className="block text-sm text-muted">
                {mode === "run" ? "Run ID" : "Proposal ID"}
                <input
                  value={targetId}
                  onChange={(event) => setTargetId(event.target.value)}
                  className="mt-2 h-10 w-full rounded-md border border-border px-3 text-sm text-ink outline-none focus:border-accent"
                  placeholder={mode === "run" ? "run_id" : "proposal_id"}
                />
              </label>
            )}
          </div>
        </Card>
        <Card title="Report">
          {report.data ? (
            <pre className="whitespace-pre-wrap text-sm leading-6 text-ink">{report.data.report}</pre>
          ) : (
            <p className="text-sm text-muted">Select a report to load evidence.</p>
          )}
        </Card>
      </div>
    </>
  );
}
