import { useMemo } from "react";
import { Square } from "lucide-react";

import ScanProgressBar from "@/components/scans/ScanProgressBar";

import Badge from "@/shared/components/Badge";
import DataTable from "@/shared/components/DataTable";
import type { Column } from "@/shared/components/DataTable";
import StatusBadge from "@/shared/components/StatusBadge";

import {
  formatScanDuration,
  scanElapsedMs,
  scanProgress,
} from "@/shared/utils/scanProgress";

import { getScanProfile } from "@/components/scans/scanProfiles";

import type { Scan } from "@/types/scan";

interface Props {
  scans: Scan[];
  loading: boolean;
  now: number;
  onSelect: (scan: Scan) => void;
  onStop: (scan: Scan) => void;
}

export default function ScanTable({ scans, loading, now, onSelect, onStop }: Props) {
  const columns: Column<Scan>[] = useMemo(
    () => [
      {
        key: "id",
        title: "Scan",
        width: "9%",
        render: (scan) => (
          <span className="font-mono text-cyan-400">#{scan.id}</span>
        ),
      },
      {
        key: "asset_name",
        title: "Asset",
        render: (scan) => (
          <div>
            <p className="font-medium text-slate-100">{scan.asset_name ?? "-"}</p>
            <p className="font-mono text-xs text-slate-500">
              asset #{scan.asset_id}
            </p>
          </div>
        ),
      },
      {
        key: "scanner",
        title: "Engine",
        width: "9%",
        render: (scan) => (
          <Badge color="blue">{scan.scanner.toUpperCase()}</Badge>
        ),
      },
      {
        key: "scan_profile",
        title: "Coverage",
        width: "10%",
        render: (scan) => {
          const meta = getScanProfile(scan.scan_profile);
          return <Badge color={meta.badge}>{meta.shortLabel}</Badge>;
        },
      },
      {
        key: "status",
        title: "Status",
        width: "10%",
        render: (scan) => <StatusBadge status={scan.status} />,
      },
      {
        key: "progress",
        title: "Progress",
        render: (scan) => (
          <ScanProgressBar
            progress={scanProgress(scan, now)}
            status={scan.status}
          />
        ),
      },
      {
        key: "elapsed",
        title: "Elapsed",
        width: "8%",
        render: (scan) =>
          scan.status === "PENDING" ? (
            <span className="text-slate-500">queued</span>
          ) : (
            <span className="font-mono text-slate-300">
              {formatScanDuration(scanElapsedMs(scan, now))}
            </span>
          ),
      },
      {
        key: "finding_count",
        title: "Findings",
        width: "9%",
        render: (scan) =>
          scan.status === "COMPLETED" ? (
            <Badge color={scan.finding_count > 0 ? "red" : "green"}>
              {scan.finding_count}
            </Badge>
          ) : (
            <span className="text-slate-500">-</span>
          ),
      },
      {
        key: "actions",
        title: "",
        width: "6%",
        render: (scan) =>
          scan.status === "RUNNING" || scan.status === "PENDING" ? (
            <button
              onClick={(event) => {
                event.stopPropagation();
                onStop(scan);
              }}
              aria-label={`Stop scan #${scan.id}`}
              title={`Stop scan #${scan.id}`}
              className="inline-flex items-center gap-1.5 rounded-lg bg-slate-800 px-2.5 py-1.5 text-xs font-semibold text-slate-300 transition hover:bg-red-600 hover:text-white"
            >
              <Square size={12} />
              Stop
            </button>
          ) : null,
      },
    ],
    [now, onStop]
  );

  return (
    <DataTable
      columns={columns}
      data={scans}
      loading={loading}
      rowKey={(scan) => scan.id}
      onRowClick={onSelect}
      emptyText="No scans match the current filters."
    />
  );
}
