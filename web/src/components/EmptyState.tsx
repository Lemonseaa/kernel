type EmptyStateProps = {
  title: string;
  body: string;
};

export function EmptyState({ title, body }: EmptyStateProps) {
  return (
    <div className="rounded-md border border-dashed border-border bg-panel p-6 text-center">
      <div className="text-sm font-semibold text-ink">{title}</div>
      <p className="mt-1 text-sm text-muted">{body}</p>
    </div>
  );
}
