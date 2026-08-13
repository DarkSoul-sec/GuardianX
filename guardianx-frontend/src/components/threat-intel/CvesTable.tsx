import { Flame } from "lucide-react";

import { Badge, DataTable } from "@/shared/components";
import type { Column } from "@/shared/components";

import { formatDate } from "@/shared/utils/format";

import type { CveSeverity, TrendingCve } from "@/types/threat-intel";

type BadgeColor = "red" | "orange" | "yellow" | "green" | "gray";

function severityBadgeColor(severity: CveSeverity): BadgeColor {
  switch (severity) {
    case "CRITICAL":
      return "red";
    case "HIGH":
      return "orange";
    case "MEDIUM":
      return "yellow";
    case "LOW":
      return "green";
    default:
      return "gray";
  }
}

function formatEpss(score: number | null): string {
  if (score === null) return "-";
  return `${Math.round(score * 100)}%`;
}

const columns: Column<TrendingCve>[] = [
  {
    key: "id",
    title: "CVE",
    render: (row) => (
      <div>
        <span className="font-mono text-sm font-bold text-cyan-300">
          {row.id}
        </span>
        {row.vendor && (
          <p className="mt-0.5 text-xs text-slate-500">{row.vendor}</p>
        )}
      </div>
    ),
  },
  {
    key: "title",
    title: "Vulnerability",
    render: (row) => (
      <span className="line-clamp-2 text-sm text-slate-200">{row.title}</span>
    ),
  },
  {
    key: "severity",
    title: "Severity",
    render: (row) => (
      <Badge color={severityBadgeColor(row.severity)}>{row.severity}</Badge>
    ),
  },
  {
    key: "cvss_score",
    title: "CVSS",
    render: (row) =>
      row.cvss_score !== null ? row.cvss_score.toFixed(1) : "-",
  },
  {
    key: "epss_score",
    title: "Exploit Likelihood",
    render: (row) => (
      <span
        className={`font-mono text-sm font-semibold ${
          row.epss_score !== null && row.epss_score >= 0.3
            ? "text-amber-300"
            : "text-slate-300"
        }`}
      >
        {formatEpss(row.epss_score)}
      </span>
    ),
  },
  {
    key: "exploited",
    title: "Status",
    render: (row) =>
      row.exploited ? (
        <Badge color="red">
          <Flame size={12} />
          Exploited
        </Badge>
      ) : (
        <Badge color="gray">Not KEV</Badge>
      ),
  },
  {
    key: "published",
    title: "Published",
    render: (row) => (
      <span className="text-sm text-slate-400">
        {formatDate(row.published)}
      </span>
    ),
  },
];

interface Props {
  items?: TrendingCve[];
  loading?: boolean;
  onSelect: (cve: TrendingCve) => void;
  emptyText?: string;
}

export default function CvesTable({
  items,
  loading,
  onSelect,
  emptyText,
}: Props) {
  return (
    <DataTable
      columns={columns}
      data={items ?? []}
      loading={loading}
      rowKey={(row) => row.id}
      onRowClick={onSelect}
      emptyText={emptyText ?? "No CVEs match your criteria."}
      ariaLabel="Threat intelligence CVE list"
    />
  );
}
