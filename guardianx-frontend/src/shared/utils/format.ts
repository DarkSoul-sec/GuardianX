/**
 * Formatting helpers used across the application.
 */

export function formatDate(value: string | Date | null | undefined): string {
  if (!value) return "-";
  const date = typeof value === "string" ? new Date(value) : value;
  if (Number.isNaN(date.getTime())) return "-";
  return date.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatDateShort(value: string | Date | null | undefined): string {
  if (!value) return "-";
  const date = typeof value === "string" ? new Date(value) : value;
  if (Number.isNaN(date.getTime())) return "-";
  return date.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function formatRelativeTime(value: string | Date | null | undefined): string {
  if (!value) return "-";
  const date = typeof value === "string" ? new Date(value) : value;
  const diffMs = date.getTime() - Date.now();
  const abs = Math.abs(diffMs);
  const seconds = Math.round(abs / 1000);
  const minutes = Math.round(seconds / 60);
  const hours = Math.round(minutes / 60);
  const days = Math.round(hours / 24);

  let label: string;
  if (seconds < 60) label = `${seconds}s`;
  else if (minutes < 60) label = `${minutes}m`;
  else if (hours < 24) label = `${hours}h`;
  else label = `${days}d`;

  return diffMs < 0 ? `${label} ago` : `in ${label}`;
}

export function formatDuration(
  startedAt: string | Date | null | undefined,
  finishedAt: string | Date | null | undefined
): string {
  if (!startedAt || !finishedAt) return "-";

  const start = new Date(startedAt).getTime();
  const end = new Date(finishedAt).getTime();

  if (Number.isNaN(start) || Number.isNaN(end) || end < start) return "-";

  const seconds = Math.max(0, Math.round((end - start) / 1000));

  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  if (minutes < 60) return `${minutes}m ${remainingSeconds}s`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h ${minutes % 60}m`;
}

export function truncate(value: string | null | undefined, length = 40): string {
  if (!value) return "-";
  return value.length > length ? `${value.slice(0, length)}…` : value;
}

export function toTitleCase(value: string | null | undefined): string {
  if (!value) return "-";
  return value
    .toLowerCase()
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined) return "-";
  return value.toLocaleString();
}
