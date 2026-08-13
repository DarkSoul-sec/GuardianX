import type { ReactNode } from "react";

import { cn } from "@/shared/utils/cn";
import { Skeleton } from "./Skeleton";

interface TimelineItem {
  id: string | number;
  title: string;
  subtitle?: string;
  timestamp?: string;
  badge?: ReactNode;
  icon?: ReactNode;
}

interface Props {
  title: string;
  items: TimelineItem[];
  loading?: boolean;
  emptyMessage?: string;
  className?: string;
}

export default function TimelineCard({
  title,
  items,
  loading = false,
  emptyMessage = "No activity yet.",
  className,
}: Props) {
  return (
    <div
      className={cn(
        "panel panel-hover rounded-2xl p-6",
        className
      )}
    >
      <h2 className="mb-5 font-display text-xl font-bold tracking-wide text-slate-100">
        {title}
      </h2>

      {loading ? (
        <div className="space-y-3">
          <Skeleton className="h-14 w-full" />
          <Skeleton className="h-14 w-full" />
          <Skeleton className="h-14 w-full" />
        </div>
      ) : items.length === 0 ? (
        <p className="text-sm text-slate-400">{emptyMessage}</p>
      ) : (
        <div className="space-y-4">
          {items.map((item) => (
            <div key={item.id} className="flex items-start gap-4">
              {item.icon && (
                <div className="mt-0.5 rounded-lg bg-cyan-500/10 p-2 text-cyan-400">
                  {item.icon}
                </div>
              )}

              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-3">
                  <p className="truncate font-semibold">{item.title}</p>
                  {item.badge}
                </div>

                {item.subtitle && (
                  <p className="mt-0.5 truncate text-sm text-slate-400">
                    {item.subtitle}
                  </p>
                )}

                {item.timestamp && (
                  <p className="mt-1 text-xs text-slate-500">{item.timestamp}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
