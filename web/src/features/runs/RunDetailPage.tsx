import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { getRun } from "../../api/client";
import { Card } from "../../components/Card";
import { JsonBlock } from "../../components/JsonBlock";
import { PageHeader } from "../../components/PageHeader";
import { StatusBadge } from "../../components/StatusBadge";

export function RunDetailPage() {
  const { id = "" } = useParams();
  const run = useQuery({ queryKey: ["run", id], queryFn: () => getRun(id), enabled: Boolean(id) });
  const data = run.data;

  return (
    <>
      <PageHeader title="Run Detail" description="Evidence record for one adapter execution." />
      <div className="grid gap-5 xl:grid-cols-[1fr_420px]">
        <Card title={data?.task ?? "Loading"}>
          {data ? (
            <div className="space-y-4 text-sm">
              <div className="flex flex-wrap gap-2">
                <StatusBadge value={data.status} />
                <span className="rounded border border-border px-2 py-0.5 text-xs text-muted">{data.scenario_id}</span>
              </div>
              <div>
                <div className="text-xs font-medium uppercase text-muted">Value Summary</div>
                <p className="mt-1 text-ink">{data.value_summary}</p>
              </div>
              <div>
                <div className="text-xs font-medium uppercase text-muted">Core Questions</div>
                <JsonBlock value={data.core_questions} />
              </div>
            </div>
          ) : (
            <p className="text-sm text-muted">Loading run.</p>
          )}
        </Card>
        <Card title="Metrics">
          <JsonBlock value={data?.metrics ?? {}} />
        </Card>
      </div>
    </>
  );
}
