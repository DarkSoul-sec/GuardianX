import { ArrowDown, ArrowUp, ChevronLeft, ChevronRight, Inbox } from "lucide-react";
import { useMemo, useState } from "react";

import { Badge, SearchInput } from "@/shared/components";
import { formatDate } from "@/shared/utils/format";

import type { IntelligenceVendorDetection } from "@/types/intelligence";

import { categoryColor } from "./labels";
import {
  filterDetections,
  sortDetections,
  type DetectionSortKey,
  type SortDirection,
} from "./threatIndicators";

interface Props {
  detections: IntelligenceVendorDetection[];
  loading?: boolean;
}

const PAGE_SIZE = 12;

const COLUMNS: {
  key: DetectionSortKey;
  title: string;
  className?: string;
}[] = [
  { key: "engine", title: "Vendor" },
  { key: "result", title: "Result" },
  { key: "category", title: "Category" },
  { key: "engine_version", title: "Engine Version" },
  { key: "update_date", title: "Update Date" },
];

function SortHeader({
  column,
  sortKey,
  direction,
  onSort,
}: {
  column: (typeof COLUMNS)[number];
  sortKey: DetectionSortKey;
  direction: SortDirection;
  onSort: (key: DetectionSortKey) => void;
}) {
  const active = sortKey === column.key;
  const Icon = active ? (direction === "asc" ? ArrowUp : ArrowDown) : ArrowDown;

  return (
    <button
      type="button"
      onClick={() => onSort(column.key)}
      className={`inline-flex items-center gap-1.5 font-mono text-xs font-semibold uppercase tracking-[0.15em] transition hover:text-cyan-300 ${
        active ? "text-cyan-300" : "text-cyan-300/70"
      }`}
    >
      {column.title}
      <Icon
        size={12}
        className={active ? "text-cyan-400" : "opacity-40"}
      />
    </button>
  );
}

export default function ThreatIndicators({ detections, loading = false }: Props) {
  const [query, setQuery] = useState("");
  const [sortKey, setSortKey] = useState<DetectionSortKey>("category");
  const [direction, setDirection] = useState<SortDirection>("asc");
  const [page, setPage] = useState(1);

  const visible = useMemo(() => {
    const filtered = filterDetections(detections, query);
    const sorted = sortDetections(filtered, sortKey, direction);
    const start = (page - 1) * PAGE_SIZE;
    return {
      items: sorted.slice(start, start + PAGE_SIZE),
      total: sorted.length,
    };
  }, [detections, query, sortKey, direction, page]);

  const pages = Math.max(1, Math.ceil(visible.total / PAGE_SIZE));

  function handleSort(key: DetectionSortKey) {
    if (key === sortKey) {
      setDirection((current) => (current === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setDirection("asc");
    }
    setPage(1);
  }

  const start = (page - 1) * PAGE_SIZE + 1;
  const end = Math.min(page * PAGE_SIZE, visible.total);

  return (
    <div className="panel overflow-hidden">
      <div className="flex flex-col gap-3 border-b border-slate-800/70 p-5 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="font-display text-xl font-bold tracking-wide text-slate-100">
            Vendor Detections
          </h2>
          <p className="mt-1 text-xs text-slate-500">
            {visible.total} engines · search and sort to analyze vendor verdicts
          </p>
        </div>

        <div className="w-full md:w-72">
          <SearchInput
            value={query}
            onChange={(value) => {
              setQuery(value);
              setPage(1);
            }}
            placeholder="Filter engines, results, categories…"
            ariaLabel="Filter vendor detections"
          />
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full">
          <caption className="sr-only">VirusTotal vendor detections</caption>
          <thead className="bg-slate-950/60">
            <tr>
              {COLUMNS.map((column) => (
                <th key={column.key} scope="col" className="px-6 py-4 text-left">
                  <SortHeader
                    column={column}
                    sortKey={sortKey}
                    direction={direction}
                    onSort={handleSort}
                  />
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              Array.from({ length: 6 }).map((_, index) => (
                <tr key={`skeleton-${index}`} className="border-t border-slate-800/70">
                  <td className="px-6 py-5" colSpan={COLUMNS.length}>
                    <div className="h-4 w-full animate-pulse rounded bg-slate-800/70" />
                  </td>
                </tr>
              ))
            ) : visible.items.length === 0 ? (
              <tr className="border-t border-slate-800/70">
                <td colSpan={COLUMNS.length} className="px-6 py-14 text-center">
                  <Inbox size={36} className="mx-auto mb-3 text-slate-600" />
                  <p className="font-display text-lg font-semibold text-slate-300">
                    No detections match
                  </p>
                  <p className="mt-1 text-sm text-slate-500">
                    Try a different filter or search term.
                  </p>
                </td>
              </tr>
            ) : (
              visible.items.map((row) => (
                <tr
                  key={row.engine}
                  className="border-t border-slate-800/70 transition hover:bg-cyan-500/[0.04]"
                >
                  <td className="px-6 py-5 font-mono text-sm font-semibold text-slate-100">
                    {row.engine}
                  </td>
                  <td className="px-6 py-5 text-sm text-slate-300">
                    {row.result ?? "-"}
                  </td>
                  <td className="px-6 py-5">
                    <Badge color={categoryColor(row.category)}>{row.category}</Badge>
                  </td>
                  <td className="px-6 py-5 font-mono text-sm text-slate-300">
                    {row.engine_version ?? "-"}
                  </td>
                  <td className="px-6 py-5 text-sm text-slate-400">
                    {formatDate(row.update_date)}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="flex flex-col items-center justify-between gap-3 border-t border-slate-800/70 p-4 text-sm text-slate-400 md:flex-row">
        <span>
          Showing <span className="font-semibold text-slate-200">{start}</span>–
          <span className="font-semibold text-slate-200">{end}</span> of{" "}
          <span className="font-semibold text-slate-200">{visible.total}</span>
        </span>

        <div className="flex items-center gap-2">
          <button
            type="button"
            disabled={page <= 1}
            onClick={() => setPage((current) => current - 1)}
            aria-label="Previous page"
            className="rounded-lg border border-slate-700/70 bg-slate-900/70 p-2 transition hover:border-cyan-500/50 hover:text-cyan-200 disabled:opacity-40"
          >
            <ChevronLeft size={16} />
          </button>
          <span className="font-mono text-xs">
            {page} / {pages}
          </span>
          <button
            type="button"
            disabled={page >= pages}
            onClick={() => setPage((current) => current + 1)}
            aria-label="Next page"
            className="rounded-lg border border-slate-700/70 bg-slate-900/70 p-2 transition hover:border-cyan-500/50 hover:text-cyan-200 disabled:opacity-40"
          >
            <ChevronRight size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
