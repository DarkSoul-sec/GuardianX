import { useEffect, useRef } from "react";
import { motion } from "framer-motion";

import { cn } from "@/shared/utils/cn";
import { formatDate } from "@/shared/utils/format";

import type { Scan } from "@/types/scan";

interface LogEntry {
  time: string;
  message: string;
  tone: "info" | "ok" | "warn" | "error" | "muted";
}

const toneClass: Record<LogEntry["tone"], string> = {
  info: "text-cyan-300",
  ok: "text-emerald-400",
  warn: "text-amber-300",
  error: "text-red-400",
  muted: "text-slate-500",
};

function buildLogEntries(scan: Scan): LogEntry[] {
  const created = scan.created_at ? formatDate(scan.created_at) : "-";
  const started = scan.started_at ? formatDate(scan.started_at) : null;
  const finished = scan.finished_at ? formatDate(scan.finished_at) : null;
  const target = scan.asset_name ?? `asset #${scan.asset_id}`;

  const entries: LogEntry[] = [
    { time: created, message: `[queue] Scan #${scan.id} submitted by scheduler`, tone: "muted" },
    { time: created, message: `[queue] Scanner engine: ${scan.scanner.toUpperCase()}`, tone: "muted" },
    { time: created, message: `[queue] Target asset: ${target}`, tone: "info" },
  ];

  if (scan.status === "PENDING") {
    entries.push({ time: "-", message: "Waiting for an available worker slot...", tone: "warn" });
    return entries;
  }

  if (started) {
    entries.push({ time: started, message: "[worker] Scan started", tone: "info" });
    entries.push({ time: started, message: `[nmap] Running scan against ${target}`, tone: "info" });
    entries.push({ time: started, message: "[nmap] Enumerating open ports...", tone: "info" });
  }

  if (scan.status === "RUNNING") {
    entries.push({ time: "-", message: "[nmap] Fingerprinting running services...", tone: "info" });
    return entries;
  }

  if (scan.status === "COMPLETED") {
    entries.push({ time: finished ?? "-", message: "[nmap] Service fingerprinting complete", tone: "ok" });
    entries.push({
      time: finished ?? "-",
      message: `[worker] ${scan.finding_count} finding${scan.finding_count === 1 ? "" : "s"} recorded`,
      tone: "ok",
    });
    entries.push({ time: finished ?? "-", message: "[worker] Scan completed successfully", tone: "ok" });
  }

  if (scan.status === "FAILED") {
    entries.push({ time: finished ?? "-", message: "[nmap] Unexpected error during execution", tone: "error" });
    entries.push({
      time: finished ?? "-",
      message: "[worker] Scan failed. Review server logs for the exception.",
      tone: "error",
    });
  }

  if (scan.status === "CANCELLED") {
    entries.push({ time: finished ?? "-", message: "[nmap] Process terminated by operator", tone: "warn" });
    entries.push({
      time: finished ?? "-",
      message: "[worker] Scan cancelled before completion.",
      tone: "warn",
    });
  }

  return entries;
}

interface Props {
  scan: Scan;
}

export default function ScanLogViewer({ scan }: Props) {
  const endRef = useRef<HTMLDivElement | null>(null);
  const entries = buildLogEntries(scan);
  const active = scan.status === "RUNNING" || scan.status === "PENDING";

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [entries.length]);

  return (
    <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-950">
      <div className="flex items-center gap-2 border-b border-slate-800 bg-slate-900 px-4 py-2.5">
        <span className="h-2.5 w-2.5 rounded-full bg-red-500" />
        <span className="h-2.5 w-2.5 rounded-full bg-yellow-500" />
        <span className="h-2.5 w-2.5 rounded-full bg-green-500" />
        <span className="ml-3 text-xs font-bold uppercase tracking-wide text-slate-400">
          Live Log {active && <span className="ml-1 animate-pulse text-cyan-400">●</span>}
        </span>
      </div>

      <div className="max-h-72 space-y-1 overflow-y-auto p-4 font-mono text-xs leading-relaxed">
        {entries.map((entry, index) => (
          <motion.div
            key={`${entry.time}-${index}`}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.25 }}
            className="flex gap-3"
          >
            <span className="shrink-0 text-slate-600">{entry.time}</span>
            <span className={cn("break-all", toneClass[entry.tone])}>{entry.message}</span>
          </motion.div>
        ))}

        {active && (
          <div className="flex items-center gap-3">
            <span className="shrink-0 text-slate-600">-</span>
            <span className="inline-block h-3.5 w-2 animate-pulse bg-cyan-400" />
          </div>
        )}

        <div ref={endRef} />
      </div>
    </div>
  );
}
