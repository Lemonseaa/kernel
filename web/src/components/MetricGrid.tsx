type MetricGridProps = {
  metrics: Array<{ label: string; value: string | number; caption?: string }>;
};

export function MetricGrid({ metrics }: MetricGridProps) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      {metrics.map((metric) => (
        <div key={metric.label} className="rounded-md border border-border bg-white p-4 shadow-surface">
          <div className="text-xs font-medium uppercase text-muted">{metric.label}</div>
          <div className="mt-2 text-2xl font-semibold text-ink">{metric.value}</div>
          {metric.caption ? <div className="mt-1 text-xs text-muted">{metric.caption}</div> : null}
        </div>
      ))}
    </div>
  );
}
