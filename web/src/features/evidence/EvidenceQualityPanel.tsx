import type { EvidenceReport } from "../../types/api";

type EvidenceQualityPanelProps = {
  report?: EvidenceReport;
};

export function EvidenceQualityPanel({ report }: EvidenceQualityPanelProps) {
  const quality = report?.evidence.quality;

  if (!quality) {
    return <p className="text-sm text-muted">No evidence quality result available.</p>;
  }

  const tone =
    quality.status === "accepted"
      ? "border-emerald-200 bg-emerald-50 text-emerald-700"
      : quality.status === "rejected"
        ? "border-red-200 bg-red-50 text-red-700"
        : "border-amber-200 bg-amber-50 text-amber-700";

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <span className={`rounded border px-2 py-0.5 text-xs font-semibold ${tone}`}>{quality.status}</span>
        <span className="text-sm text-muted">score {quality.score.toFixed(2)}</span>
      </div>
      {quality.reasons.length ? (
        <ul className="space-y-1 text-sm text-ink">
          {quality.reasons.map((reason) => (
            <li key={reason} className="rounded-md border border-border bg-panel px-3 py-2">
              {reason}
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-muted">No quality warnings.</p>
      )}
    </div>
  );
}
