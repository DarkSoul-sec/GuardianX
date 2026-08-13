import type { Scan } from "@/types/scan";

/**
 * Deterministic, client-side scan progress estimation.
 *
 * The engine does not stream progress percentages, so live progress is
 * derived from the real lifecycle timestamps and a baseline duration.
 * Completed and failed scans always resolve to a definitive state.
 */

export const SCAN_BASELINE_MS = 90_000;

const MAX_ESTIMATED_PROGRESS = 92;

function scanStartMs(scan: Scan, now: number): number {
  const start = scan.started_at
    ? new Date(scan.started_at).getTime()
    : new Date(scan.created_at).getTime();

  return Number.isNaN(start) ? now : start;
}

export function scanProgress(scan: Scan, now: number): number {
  switch (scan.status) {
    case "COMPLETED":
    case "FAILED":
    case "CANCELLED":
      return 100;
    case "PENDING":
      return 5;
    case "RUNNING": {
      const elapsed = Math.max(0, now - scanStartMs(scan, now));
      return Math.min(
        MAX_ESTIMATED_PROGRESS,
        Math.round((elapsed / SCAN_BASELINE_MS) * 100)
      );
    }
  }
}

export function scanElapsedMs(scan: Scan, now: number): number {
  const start = scanStartMs(scan, now);

  if (scan.status === "COMPLETED" || scan.status === "FAILED" || scan.status === "CANCELLED") {
    const finished = scan.finished_at
      ? new Date(scan.finished_at).getTime()
      : now;
    return Math.max(0, finished - start);
  }

  return Math.max(0, now - start);
}

export function formatScanDuration(ms: number): string {
  if (ms < 1000) return "<1s";
  const seconds = Math.round(ms / 1000);
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ${seconds % 60}s`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h ${minutes % 60}m`;
}

export function scanEta(scan: Scan, now: number): string | null {
  if (
    scan.status === "COMPLETED" ||
    scan.status === "FAILED" ||
    scan.status === "CANCELLED"
  )
    return null;
  if (scan.status === "PENDING") return "Waiting for scheduler";

  const elapsed = Math.max(0, now - scanStartMs(scan, now));
  const remaining = Math.max(0, SCAN_BASELINE_MS - elapsed);

  if (remaining === 0) return "Any moment now";

  const minutes = Math.ceil(remaining / 60_000);
  return `~${minutes} min${minutes === 1 ? "" : "s"} remaining`;
}
