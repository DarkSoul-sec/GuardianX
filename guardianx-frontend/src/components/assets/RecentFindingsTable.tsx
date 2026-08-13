import { Bug } from "lucide-react";

import CvssBadge from "@/shared/components/CvssBadge";
import SeverityBadge from "@/shared/components/SeverityBadge";
import StatusBadge from "@/shared/components/StatusBadge";

import Card from "@/shared/components/Card";
import DataTable from "@/shared/components/DataTable";
import type { Column } from "@/shared/components/DataTable";

import { truncate } from "@/shared/utils/format";

import type { AssetDetails, AssetRecentFinding } from "@/types/asset";

const columns: Column<AssetRecentFinding>[] = [
  {
    key: "cve",
    title: "CVE",
    width: "10%",
    render: (row) =>
      row.cve ? (
        <span className="font-mono text-cyan-400">{row.cve}</span>
      ) : (
        <span className="text-slate-500">-</span>
      ),
  },
  {
    key: "title",
    title: "Finding",
    render: (row) => (
      <div>
        <p className="font-medium text-slate-100">{truncate(row.title, 60)}</p>
        {row.recommendation && (
          <p className="mt-0.5 max-w-xl text-xs text-slate-500">
            {truncate(row.recommendation, 100)}
          </p>
        )}
      </div>
    ),
  },
  {
    key: "severity",
    title: "Severity",
    width: "10%",
    render: (row) => <SeverityBadge severity={row.severity} />,
  },
  {
    key: "cvss",
    title: "CVSS",
    width: "8%",
    render: (row) => <CvssBadge score={row.cvss} />,
  },
  {
    key: "status",
    title: "Status",
    width: "12%",
    render: (row) => <StatusBadge status={row.status} />,
  },
];

interface Props {
  asset: AssetDetails;
}

export default function RecentFindingsTable({ asset }: Props) {
  return (
    <Card className="space-y-5">
      <div className="flex items-center gap-2">
        <div className="rounded-xl bg-cyan-500/10 p-2 text-cyan-400">
          <Bug size={18} />
        </div>
        <div>
          <h2 className="text-xl font-bold">Recent Findings</h2>
          <p className="text-sm text-slate-400">
            Latest 10 vulnerabilities detected on this asset.
          </p>
        </div>
      </div>

      <DataTable
        columns={columns}
        data={asset.recent_findings}
        rowKey={(row) => `${row.cve ?? "finding"}-${row.title}`}
        emptyText="No findings recorded for this asset."
      />
    </Card>
  );
}
