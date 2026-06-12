import type { WorkflowVisualization } from "../../types/api";

type WorkflowMapProps = {
  visualization: WorkflowVisualization;
  selectedNodeId: string;
  onSelectNode: (nodeId: string) => void;
};

export function WorkflowMap({ visualization, selectedNodeId, onSelectNode }: WorkflowMapProps) {
  const path = visualization.run_path.join(" → ") || "-";

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div>
          <div className="text-xs font-medium uppercase text-muted">Run path</div>
          <p className="mt-1 text-ink">{path}</p>
        </div>
        <div>
          <div className="text-xs font-medium uppercase text-muted">Black boxes</div>
          <p className="mt-1 text-ink">{visualization.black_box_node_ids.join(", ") || "None"} </p>
        </div>
      </div>

      <div className="flex flex-wrap gap-2 text-xs">
        <Legend label="Traced" className="border-emerald-200 bg-emerald-50 text-emerald-700" />
        <Legend label="Metric" className="border-blue-200 bg-blue-50 text-blue-700" />
        <Legend label="Black box" className="border-amber-200 bg-amber-50 text-amber-700" />
        <Legend label="Error" className="border-red-200 bg-red-50 text-red-700" />
      </div>

      <div className="flex flex-wrap items-stretch gap-2">
        {visualization.nodes.map((node, index) => (
          <div key={node.id} className="flex items-center gap-2">
            <button
              className={`min-w-36 rounded-md border p-3 text-left text-sm transition ${
                node.id === selectedNodeId ? "border-accent bg-blue-50" : "border-border bg-white hover:border-accent"
              }`}
              onClick={() => onSelectNode(node.id)}
            >
              <div className="font-semibold text-ink">{node.name || node.id}</div>
              <div className="mt-1 flex flex-wrap gap-1">
                <NodeBadge label={node.type} />
                {visualization.traced_node_ids.includes(node.id) ? <NodeBadge label="Traced" tone="green" /> : null}
                {visualization.metric_node_ids.includes(node.id) ? <NodeBadge label="Metric" tone="blue" /> : null}
                {visualization.black_box_node_ids.includes(node.id) ? <NodeBadge label="Black box" tone="amber" /> : null}
                {visualization.error_node_ids.includes(node.id) ? <NodeBadge label="Error" tone="red" /> : null}
              </div>
            </button>
            {index < visualization.nodes.length - 1 ? <span className="text-muted">→</span> : null}
          </div>
        ))}
      </div>
    </div>
  );
}

type BadgeTone = "neutral" | "green" | "blue" | "amber" | "red";

function NodeBadge({ label, tone = "neutral" }: { label: string; tone?: BadgeTone }) {
  const className = {
    neutral: "border-border bg-panel text-muted",
    green: "border-emerald-200 bg-emerald-50 text-emerald-700",
    blue: "border-blue-200 bg-blue-50 text-blue-700",
    amber: "border-amber-200 bg-amber-50 text-amber-700",
    red: "border-red-200 bg-red-50 text-red-700"
  }[tone];

  return <span className={`rounded border px-1.5 py-0.5 text-xs font-medium ${className}`}>{label}</span>;
}

function Legend({ label, className }: { label: string; className: string }) {
  return <span className={`rounded border px-2 py-0.5 font-medium ${className}`}>{label}</span>;
}
