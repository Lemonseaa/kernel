export function formatDate(value?: string) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

export function shortId(value: string) {
  return value.length > 10 ? `${value.slice(0, 8)}…` : value;
}

export function stringifyJson(value: unknown) {
  return JSON.stringify(value ?? {}, null, 2);
}
