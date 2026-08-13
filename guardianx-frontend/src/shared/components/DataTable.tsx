import type { KeyboardEvent, ReactNode } from "react";
import { Inbox } from "lucide-react";

import EmptyState from "@/shared/components/EmptyState";
import { TableSkeleton } from "@/shared/components/TableSkeleton";

export interface Column<T> {
  key: keyof T | string;
  title: string;
  width?: string;
  render?: (row: T) => ReactNode;
  headerRender?: () => ReactNode;
}

interface Props<T> {
  columns: Column<T>[];
  data: T[];
  loading?: boolean;
  emptyText?: string;
  rowKey: (row: T) => string | number;
  onRowClick?: (row: T) => void;
  ariaLabel?: string;
}

export default function DataTable<T>({
  columns,
  data,
  loading = false,
  emptyText = "No data available.",
  rowKey,
  onRowClick,
  ariaLabel = "Data table",
}: Props<T>) {
  if (loading) {
    return (
      <TableSkeleton rows={4} columns={Math.max(columns.length, 3)} />
    );
  }

  if (!data.length) {
    return (
      <EmptyState
        title={emptyText}
        icon={<Inbox size={40} />}
      />
    );
  }

  function handleRowKeyDown(event: KeyboardEvent<HTMLTableRowElement>, row: T) {
    if (!onRowClick) return;
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      onRowClick(row);
    }
  }

  const interactive = Boolean(onRowClick);

  return (
    <div className="panel overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full">
          <caption className="sr-only">{ariaLabel}</caption>
          <thead className="bg-slate-950/60">
            <tr>
              {columns.map((column) => (
                <th
                  key={column.title}
                  scope="col"
                  style={{ width: column.width }}
                  className="px-6 py-4 text-left font-mono text-xs font-semibold uppercase tracking-[0.15em] text-cyan-300/70"
                >
                  {column.headerRender ? column.headerRender() : column.title}
                </th>
              ))}
            </tr>
          </thead>

          <tbody>
            {data.map((row) => (
              <tr
                key={rowKey(row)}
                onClick={() => onRowClick?.(row)}
                onKeyDown={(event) => handleRowKeyDown(event, row)}
                tabIndex={interactive ? 0 : undefined}
                className={`group border-t border-slate-800/70 transition hover:bg-cyan-500/[0.04] ${
                  interactive
                    ? "cursor-pointer focus:outline-none focus:bg-cyan-500/[0.06]"
                    : ""
                }`}
              >
                {columns.map((column) => (
                  <td
                    key={String(column.key)}
                    className="px-6 py-5 text-slate-200"
                  >
                    {column.render
                      ? column.render(row)
                      : String(row[column.key as keyof T] ?? "-")}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
