import { stringifyJson } from "../lib/format";

type JsonBlockProps = {
  value: unknown;
};

export function JsonBlock({ value }: JsonBlockProps) {
  return (
    <pre className="max-h-[420px] overflow-auto rounded-md border border-border bg-slate-950 p-3 text-xs leading-5 text-slate-100">
      {stringifyJson(value)}
    </pre>
  );
}
