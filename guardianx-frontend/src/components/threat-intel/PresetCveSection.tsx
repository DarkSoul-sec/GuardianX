import type { ReactNode } from "react";

import CvesTable from "@/components/threat-intel/CvesTable";
import { useThreatIntelSearch } from "@/hooks/useThreatIntel";
import type {
  ThreatIntelSearchFilters,
  TrendingCve,
} from "@/types/threat-intel";

interface Props {
  title: string;
  subtitle: string;
  icon?: ReactNode;
  accent?: "red" | "amber" | "cyan";
  filters: ThreatIntelSearchFilters;
  onSelect: (cve: TrendingCve) => void;
  emptyText?: string;
}

function accentClasses(accent: Props["accent"]): string {
  switch (accent) {
    case "red":
      return "border-l-rose-500";
    case "amber":
      return "border-l-amber-500";
    case "cyan":
      return "border-l-cyan-400";
    default:
      return "border-l-slate-600";
  }
}

export default function PresetCveSection({
  title,
  subtitle,
  icon,
  accent,
  filters,
  onSelect,
  emptyText,
}: Props) {
  const { data, isLoading } = useThreatIntelSearch(filters, true);

  return (
    <section
      className={`rounded-xl border border-slate-800 bg-slate-900/40 border-l-4 ${accentClasses(accent)} p-5`}
    >
      <div className="mb-4 flex items-center justify-between gap-2">
        <div>
          <h3 className="flex items-center gap-2 text-base font-bold text-white">
            {icon}
            {title}
          </h3>
          <p className="mt-0.5 text-xs text-slate-400">{subtitle}</p>
        </div>
        <span className="text-xs text-slate-500">{data?.total ?? 0}</span>
      </div>
      <CvesTable
        items={data?.items}
        loading={isLoading}
        onSelect={onSelect}
        emptyText={emptyText ?? "No CVEs match this section."}
      />
    </section>
  );
}
