import { useQuery } from "@tanstack/react-query";
import { listLearningObservations, listSafetyFindings, listValidationSummaries } from "../../api/client";
import { Card } from "../../components/Card";
import { DataTable } from "../../components/DataTable";
import { EmptyState } from "../../components/EmptyState";
import { JsonBlock } from "../../components/JsonBlock";
import { PageHeader } from "../../components/PageHeader";
import type { LearningObservation, SafetyFinding, ValidationSummary } from "../../types/api";

export function LearningPage() {
  const observations = useQuery({ queryKey: ["learning", "observations"], queryFn: listLearningObservations });
  const safety = useQuery({ queryKey: ["learning", "safety"], queryFn: listSafetyFindings });
  const validations = useQuery({ queryKey: ["learning", "validations"], queryFn: listValidationSummaries });

  return (
    <>
      <PageHeader title="Learning Loop" description="Observations, safety findings, and validation records." />
      <div className="grid gap-4 xl:grid-cols-2">
        <Card title="Observations">
          {observations.data?.length ? (
            <DataTable<LearningObservation>
              rows={observations.data}
              columns={[
                { key: "title", header: "Title", render: (row) => row.title },
                { key: "severity", header: "Severity", render: (row) => row.severity },
                { key: "summary", header: "Summary", render: (row) => row.summary }
              ]}
            />
          ) : (
            <EmptyState title="No observations" body="Run the learning loop after scenario runs have metrics." />
          )}
        </Card>
        <Card title="Safety Findings">
          {safety.data?.length ? (
            <DataTable<SafetyFinding>
              rows={safety.data}
              columns={[
                { key: "severity", header: "Severity", render: (row) => row.severity },
                { key: "proposal", header: "Proposal", render: (row) => row.proposal_id },
                { key: "reason", header: "Reason", render: (row) => row.reason }
              ]}
            />
          ) : (
            <EmptyState title="No safety findings" body="Blocked or risky proposals will appear here." />
          )}
        </Card>
      </div>
      <div className="mt-4">
        <Card title="Validation Summaries">
          {validations.data?.length ? (
            <DataTable<ValidationSummary>
              rows={validations.data}
              columns={[
                { key: "proposal", header: "Proposal", render: (row) => row.proposal_id },
                { key: "improved", header: "Improved", render: (row) => (row.improved ? "yes" : "no") },
                { key: "recommendation", header: "Recommendation", render: (row) => row.recommendation },
                { key: "diff", header: "Metric Diff", render: (row) => <JsonBlock value={row.metric_diffs} /> }
              ]}
            />
          ) : (
            <EmptyState title="No validation summaries" body="Shadow or replay validation results will appear here." />
          )}
        </Card>
      </div>
    </>
  );
}
