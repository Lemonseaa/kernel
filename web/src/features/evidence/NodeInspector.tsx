import type { WorkflowVisualization } from "../../types/api";

type NodeInspectorProps = {
  visualization?: WorkflowVisualization;
  nodeId: string;
};

export function NodeInspector({ visualization, nodeId }: NodeInspectorProps) {
  const node = visualization?.nodes.find((item) => item.id === nodeId);

  if (!visualization || !node) {
    return <p className="text-sm text-muted">Select a workflow node to inspect evidence.</p>;
  }

  const traced = visualization.traced_node_ids.includes(node.id);
  const metricCaptured = visualization.metric_node_ids.includes(node.id);
  const blackBox = visualization.black_box_node_ids.includes(node.id);
  const error = visualization.error_node_ids.includes(node.id);
  const latency = visualization.node_latencies_ms[node.id];
  const cost = visualization.node_costs[node.id];

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-3 text-sm">
        <Detail label="Node id" value={node.id} />
        <Detail label="Type" value={node.type} />
        <Detail label="Latency" value={latency === undefined ? "-" : `${latency} ms`} />
        <Detail label="Cost" value={cost === undefined ? "-" : `$${cost.toFixed(3)}`} />
      </div>

      <div className="flex flex-wrap gap-2 text-xs">
        <Status label={traced ? "Traced" : "Trace missing"} tone={traced ? "green" : "amber"} />
        <Status label={metricCaptured ? "Metric captured" : "Metric missing"} tone={metricCaptured ? "blue" : "amber"} />
        {blackBox ? <Status label="Black-box node" tone="amber" /> : null}
        {error ? <Status label="Error node" tone="red" /> : null}
      </div>
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xs font-medium uppercase text-muted">{label}</div>
      <p className="mt-1 text-ink">{value}</p>
    </div>
  );
}

function Status({ label, tone }: { label: string; tone: "green" | "blue" | "amber" | "red" }) {
  const className = {
    green: "border-emerald-200 bg-emerald-50 text-emerald-700",
    blue: "border-blue-200 bg-blue-50 text-blue-700",
    amber: "border-amber-200 bg-amber-50 text-amber-700",
    red: "border-red-200 bg-red-50 text-red-700"
  }[tone];

  return <span className={`rounded border px-2 py-0.5 font-medium ${className}`}>{label}</span>;
}
