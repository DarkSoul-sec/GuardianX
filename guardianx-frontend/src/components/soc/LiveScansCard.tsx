import { Activity, Inbox } from "lucide-react";

import { Badge, Skeleton } from "@/shared/components";
import type { LiveScan } from "@/types/soc";

interface Props {
  scans: LiveScan[];
  loading?: boolean;
}

function statusColor(status: string) {
  if (status === "RUNNING") return "cyan" as const;
  if (status === "PENDING") return "yellow" as const;
  return "gray" as const;
}

function formatElapsed(seconds: number | null): string {
  if (seconds === null) return "-";
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  if (minutes < 60) return `${minutes}m ${remainingSeconds}s`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h ${minutes % 60}m`;
}

export default function LiveScansCard({ scans, loading = false }: Props) {
  const running = scans.filter((s) => s.status === "RUNNING").length;

  return (
    <div className="panel panel-hover rounded-2xl p-6">
      <div className="mb-5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity size={18} className="text-cyan-400" />
          <h2 className="font-display text-lg font-semibold tracking-wide text-slate-100">
            Live Scans
          </h2>
        </div>
        {running > 0 && (
          <span className="flex items-center gap-2 font-mono text-xs text-cyan-300">
            <span className="h-2 w-2 animate-pulse rounded-full bg-cyan-400 shadow-[0_0_8px_rgba(0,207,255,0.9)]" />
            {running} running
          </span>
        )}
      </div>

      {loading ? (
        <div className="space-y-3">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
        </div>
      ) : scans.length === 0 ? (
        <div className="flex flex-col items-center py-10 text-slate-500">
          <Inbox size={26} />
          <p className="mt-2 text-sm">No scans in progress.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {scans.map((scan) => (
            <div
              key={scan.scan_id}
              className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-900/40 px-4 py-3"
            >
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-slate-200">
                  {scan.asset_name}
                </p>
                <p className="font-mono text-[11px] text-slate-500">
                  Scan #{scan.scan_id}
                </p>
              </div>

              <div className="flex shrink-0 items-center gap-3">
                {scan.elapsed_seconds !== null && (
                  <span className="font-mono text-xs text-slate-400">
                    {formatElapsed(scan.elapsed_seconds)}
                  </span>
                )}
                <Badge color={statusColor(scan.status)}>{scan.status}</Badge>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}