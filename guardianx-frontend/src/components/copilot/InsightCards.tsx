import {
  FileWarning,
  Server,
  Cable,
  Bug,
} from "lucide-react";

import Badge from "@/shared/components/Badge";
import { cn } from "@/shared/utils/cn";

import type { CopilotResultItem } from "@/types/copilot";

interface Props {
  results: CopilotResultItem[];
}

const KIND_ICONS = {
  finding: FileWarning,
  asset: Server,
  service: Cable,
  cve: Bug,
} as const;

const SEVERITY_COLORS: Record<string, "red" | "orange" | "yellow" | "green" | "blue" | "gray"> = {
  CRITICAL: "red",
  HIGH: "orange",
  MEDIUM: "yellow",
  LOW: "green",
};

function ResultCard({ item }: { item: CopilotResultItem }) {
  const Icon = KIND_ICONS[item.kind] ?? FileWarning;
  const severity = item.severity?.toUpperCase();

  return (
    <div className="flex items-start gap-3 rounded-xl border border-slate-800 bg-slate-900/60 px-4 py-3 transition hover:border-cyan-500/40">
      <span
        className={cn(
          "mt-0.5 rounded-lg p-2",
          item.kind === "finding"
            ? "bg-red-500/10 text-red-400"
            : "bg-slate-800 text-slate-300"
        )}
      >
        <Icon size={16} />
      </span>

      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="truncate font-semibold text-white">
            {item.title}
          </span>
          {severity && (
            <Badge color={SEVERITY_COLORS[severity] ?? "gray"}>
              {item.severity}
            </Badge>
          )}
        </div>

        {item.detail && (
          <p className="mt-0.5 truncate text-xs text-slate-400">
            {item.detail}
          </p>
        )}

        {(item.status || item.score) && (
          <div className="mt-1.5 flex flex-wrap items-center gap-2 text-[11px] text-slate-500">
            {item.status && (
              <span className="capitalize">Status: {item.status.toLowerCase()}</span>
            )}
            {item.score && <span>Score: {item.score}</span>}
          </div>
        )}
      </div>
    </div>
  );
}

export default function InsightCards({ results }: Props) {
  if (!results.length) return null;

  const byKind = results.reduce<Record<string, number>>((acc, item) => {
    acc[item.kind] = (acc[item.kind] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <div className="mt-3 rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Structured results
        </span>
        {Object.entries(byKind).map(([kind, count]) => (
          <span
            key={kind}
            className="rounded-full bg-slate-800 px-2 py-0.5 text-[10px] font-semibold uppercase text-slate-400"
          >
            {count} {kind}
          </span>
        ))}
      </div>

      <div className="grid gap-2">
        {results.map((item, index) => (
          <ResultCard key={`${item.kind}-${item.id ?? index}-${index}`} item={item} />
        ))}
      </div>
    </div>
  );
}
