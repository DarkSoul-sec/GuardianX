import {
  History,
  RotateCcw,
  SearchX,
  Trash2,
} from "lucide-react";

import {
  Badge,
  Button,
  EmptyState,
  Pagination,
  SearchInput,
  Select,
  Skeleton,
} from "@/shared/components";
import { formatRelativeTime } from "@/shared/utils/format";

import type {
  IntelligenceHistoryResponse,
  IntelligenceIocType,
} from "@/types/intelligence";

import { IOC_META } from "./ioc";
import { THREAT_LEVEL_META } from "./labels";

interface Props {
  data?: IntelligenceHistoryResponse;
  loading: boolean;
  iocTypeFilter: string;
  query: string;
  onIocTypeFilterChange: (value: string) => void;
  onQueryChange: (value: string) => void;
  onPageChange: (page: number) => void;
  onSearchAgain: (resource: string) => void;
  onDelete: (id: number) => void;
  onClearAll: () => void;
}

const TYPE_OPTIONS: { value: string; label: string }[] = [
  { value: "", label: "All types" },
  ...Object.entries(IOC_META).map(([value, meta]) => ({
    value,
    label: meta.label,
  })),
];

export default function ThreatHistory({
  data,
  loading,
  iocTypeFilter,
  query,
  onIocTypeFilterChange,
  onQueryChange,
  onPageChange,
  onSearchAgain,
  onDelete,
  onClearAll,
}: Props) {
  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const pages = Math.max(1, Math.ceil(total / (data?.limit ?? 10)));

  return (
    <div className="panel panel-hover overflow-hidden">
      <div className="flex flex-col gap-3 border-b border-slate-800/70 p-5 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="flex items-center gap-2 font-display text-xl font-bold tracking-wide text-slate-100">
            <History size={20} className="text-cyan-400" />
            Threat History
          </h2>
          <p className="mt-1 text-xs text-slate-500">
            {total} saved {total === 1 ? "search" : "searches"}
          </p>
        </div>

        <div className="flex flex-col gap-2 sm:flex-row">
          <Select
            value={iocTypeFilter}
            onChange={(event) => {
              onIocTypeFilterChange(event.target.value);
              onPageChange(1);
            }}
            aria-label="Filter by IOC type"
            className="sm:w-44"
          >
            {TYPE_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>

          <div className="sm:w-56">
            <SearchInput
              value={query}
              onChange={(value) => {
                onQueryChange(value);
                onPageChange(1);
              }}
              placeholder="Search history…"
              ariaLabel="Search threat history"
            />
          </div>

          <Button
            variant="danger"
            onClick={onClearAll}
            disabled={total === 0}
          >
            <Trash2 size={16} className="mr-2 inline" />
            Clear All
          </Button>
        </div>
      </div>

      {loading ? (
        <div className="space-y-3 p-5">
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-16 w-full" />
        </div>
      ) : items.length === 0 ? (
        <EmptyState
          title="No search history"
          description={
            query || iocTypeFilter
              ? "No history matches your filters."
              : "Every indicator you analyze is saved here for quick re-runs."
          }
          icon={<SearchX size={40} />}
          className="border-0"
        />
      ) : (
        <>
          <ul className="divide-y divide-slate-800/70">
            {items.map((item) => (
              <li
                key={item.id}
                className="flex flex-col gap-3 p-5 transition hover:bg-cyan-500/[0.03] md:flex-row md:items-center md:justify-between"
              >
                <div className="min-w-0">
                  <p className="break-all font-mono text-sm font-semibold text-slate-100">
                    {item.resource}
                  </p>
                  <div className="mt-2 flex flex-wrap items-center gap-2">
                    <Badge color="cyan">
                      {IOC_META[item.resource_type as IntelligenceIocType].label}
                    </Badge>
                    <Badge color={THREAT_LEVEL_META[item.threat_level].color}>
                      {THREAT_LEVEL_META[item.threat_level].label}
                    </Badge>
                    {item.detected ? (
                      <Badge color="red">Detected</Badge>
                    ) : (
                      <Badge color="green">Clean</Badge>
                    )}
                    <span className="font-mono text-xs text-slate-500">
                      {item.detection_ratio}
                    </span>
                    <span className="text-xs text-slate-500">
                      {formatRelativeTime(item.created_at)}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Button
                    variant="secondary"
                    onClick={() => onSearchAgain(item.resource)}
                  >
                    <RotateCcw size={14} className="mr-2 inline" />
                    Search Again
                  </Button>
                  <button
                    type="button"
                    aria-label={`Delete ${item.resource} from history`}
                    onClick={() => onDelete(item.id)}
                    className="rounded-lg border border-slate-700/70 bg-slate-900/70 p-2.5 text-slate-400 transition hover:border-rose-500/50 hover:text-rose-300"
                  >
                    <Trash2 size={15} />
                  </button>
                </div>
              </li>
            ))}
          </ul>

          <Pagination page={data?.page ?? 1} pages={pages} onChange={onPageChange} />
        </>
      )}
    </div>
  );
}
