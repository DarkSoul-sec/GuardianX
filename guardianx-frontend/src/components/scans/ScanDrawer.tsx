import { Cpu, FolderSearch, Gauge, Timer } from "lucide-react";

import ScanLogViewer from "@/components/scans/ScanLogViewer";
import ScanProgressBar from "@/components/scans/ScanProgressBar";
import { getScanProfile } from "@/components/scans/scanProfiles";

import {
  DataTable,
  Drawer,
  Skeleton,
  StatusBadge,
  TimelineCard,
} from "@/shared/components";

import {
  formatScanDuration,
  scanElapsedMs,
  scanEta,
  scanProgress,
} from "@/shared/utils/scanProgress";
import { formatDate } from "@/shared/utils/format";

import { useNow } from "@/hooks/useNow";
import { useScanResults } from "@/hooks/useScans";

import type { Scan, ScanResult } from "@/types/scan";

interface FactProps {
  label: string;
  value: string;
}

function Fact({ label, value }: FactProps) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 break-words font-semibold text-slate-100">{value}</p>
    </div>
  );
}

interface Props {
  scan: Scan | null;
  onClose: () => void;
}

export default function ScanDrawer({ scan, onClose }: Props) {
  const now = useNow(1000);

  const { data: results = [], isLoading: resultsLoading } = useScanResults(
    scan?.id ?? 0,
    { enabled: !!scan && scan.status === "COMPLETED" },
  );

  if (!scan) return null;

  return (
    <Drawer open={!!scan} onClose={onClose} titleId="scan-drawer-title">
      <div className="mb-8 flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h2 id="scan-drawer-title" className="text-3xl font-bold">
              Scan <span className="font-mono text-cyan-400">#{scan.id}</span>
            </h2>
              <StatusBadge status={scan.status} />
            </div>
            <p className="mt-1 text-slate-400">Scan Operations Center</p>
          </div>

          <button
            onClick={onClose}
            className="rounded-lg bg-slate-800 px-4 py-2 transition hover:bg-slate-700"
          >
            Close
          </button>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold uppercase tracking-wide text-slate-400">
              Scan Progress
            </h3>
            <Gauge size={18} className="text-cyan-400" />
          </div>

          <div className="mt-4">
            <ScanProgressBar
              progress={scanProgress(scan, now)}
              status={scan.status}
            />
          </div>

          <div className="mt-4 grid grid-cols-2 gap-4">
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <Timer size={14} />
              <span>
                Elapsed:{" "}
                <span className="font-mono text-slate-200">
                  {formatScanDuration(scanElapsedMs(scan, now))}
                </span>
              </span>
            </div>
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <Gauge size={14} />
              <span>
                ETA:{" "}
                <span className="font-mono text-slate-200">
                  {scanEta(scan, now)}
                </span>
              </span>
            </div>
          </div>
        </div>

        <div className="mt-6 grid grid-cols-2 gap-4">
          <Fact label="Asset" value={scan.asset_name ?? `Asset #${scan.asset_id}`} />
          <div className="flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-900 p-4">
            <Cpu size={16} className="shrink-0 text-cyan-400" />
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-500">Scanner Engine</p>
              <p className="mt-2 font-semibold text-slate-100">
                {scan.scanner.toUpperCase()}
              </p>
            </div>
          </div>
          <Fact label="Coverage" value={getScanProfile(scan.scan_profile).label} />
          <Fact label="Findings" value={String(scan.finding_count)} />
          <Fact label="Created" value={formatDate(scan.created_at)} />
        </div>

        <div className="mt-6">
          <div className="mb-3 flex items-center gap-2">
            <h3 className="text-xl font-bold">Discovered Services</h3>
            <span className="text-xs text-slate-500">
              {results.length} result{results.length === 1 ? "" : "s"}
            </span>
          </div>
          <DataTable<ScanResult>
            ariaLabel="Discovered services"
            columns={[
              {
                key: "port",
                title: "Port",
                width: "140px",
                render: (row) => (
                  <span className="font-mono text-cyan-400">
                    {row.port}/{row.protocol}
                  </span>
                ),
              },
              { key: "state", title: "State" },
              {
                key: "service",
                title: "Service",
                render: (row) => row.service ?? "—",
              },
              {
                key: "product",
                title: "Product",
                render: (row) => row.product ?? "—",
              },
              {
                key: "version",
                title: "Version",
                render: (row) => row.version ?? "—",
              },
            ]}
            data={results}
            loading={resultsLoading}
            emptyText="No open services were discovered on this scan."
            rowKey={(row) => String(row.id)}
          />
        </div>

        <div className="mt-6">
          <TimelineCard
            title="Scan Timeline"
            items={[
              {
                id: "created",
                title: "Scan created",
                subtitle: `Asset: ${scan.asset_name ?? `#${scan.asset_id}`}`,
                timestamp: formatDate(scan.created_at),
                icon: <FolderSearch size={16} />,
              },
              {
                id: "started",
                title: "Execution started",
                subtitle: `Engine: ${scan.scanner.toUpperCase()}`,
                timestamp: formatDate(scan.started_at),
                icon: <Cpu size={16} />,
              },
              ...(scan.status === "RUNNING"
                ? [
                    {
                      id: "running",
                      title: "In progress",
                      subtitle: "Scanning target asset...",
                      timestamp: "live",
                      icon: <Timer size={16} />,
                    },
                  ]
                : scan.status === "FAILED"
                  ? [
                      {
                        id: "failed",
                        title: "Failed",
                        subtitle: "Execution stopped unexpectedly",
                        timestamp: formatDate(scan.finished_at),
                        icon: <span />,
                      },
                    ]
                  : [
                      {
                        id: "completed",
                        title: "Completed",
                        subtitle: `${scan.finding_count} finding${scan.finding_count === 1 ? "" : "s"} recorded`,
                        timestamp: formatDate(scan.finished_at),
                        icon: <span />,
                      },
                    ]),
            ]}
            emptyMessage="No timeline events."
          />
        </div>

        <div className="mt-6">
          <div className="mb-3 flex items-center gap-2">
            <h3 className="text-xl font-bold">Live Logs</h3>
            <span className="h-2 w-2 animate-pulse rounded-full bg-cyan-400" />
          </div>
          <ScanLogViewer scan={scan} />
        </div>

        {scan.status === "RUNNING" && (
          <div className="mt-6 flex items-center gap-2 text-xs text-slate-500">
            <Skeleton className="h-3 w-3 rounded-full" />
            Refreshing automatically. Data updates every few seconds.
          </div>
        )}
    </Drawer>
  );
}
