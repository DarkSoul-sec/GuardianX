import { Skeleton } from "./Skeleton";

import { cn } from "@/shared/utils/cn";

interface Props {
  rows?: number;
  columns?: number;
  className?: string;
}

export function TableSkeleton({ rows = 5, columns = 4, className }: Props) {
  return (
    <div
      aria-hidden="true"
      className={cn(
        "overflow-hidden rounded-2xl border border-slate-800 bg-slate-900",
        className
      )}
    >
      <div className="flex gap-4 border-b border-slate-800 bg-slate-950 px-6 py-4">
        {Array.from({ length: columns }).map((_, index) => (
          <Skeleton key={index} className={cn("h-4", index === 0 ? "w-32" : "w-24")} />
        ))}
      </div>

      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div
          key={rowIndex}
          className="flex gap-4 border-b border-slate-800/50 px-6 py-5 last:border-0"
        >
          {Array.from({ length: columns }).map((_, columnIndex) => (
            <Skeleton
              key={columnIndex}
              className={cn("h-4", columnIndex === 0 ? "w-1/3" : "flex-1")}
            />
          ))}
        </div>
      ))}
    </div>
  );
}
