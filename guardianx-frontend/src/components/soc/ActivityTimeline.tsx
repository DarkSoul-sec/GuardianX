import { History, Inbox } from "lucide-react";

import { Skeleton } from "@/shared/components";
import { formatRelativeTime } from "@/shared/utils/format";
import { getActivityMeta } from "./ActivityMeta";
import type { ActivityItem } from "@/types/soc";

interface Props {
  title?: string;
  items: ActivityItem[];
  loading?: boolean;
  limit?: number;
}

export default function ActivityTimeline({
  title = "Activity Timeline",
  items,
  loading = false,
  limit = 8,
}: Props) {
  const visible = items.slice(0, limit);

  return (
    <div className="panel panel-hover rounded-2xl p-6">
      <div className="mb-5 flex items-center gap-2">
        <History size={18} className="text-cyan-400" />
        <h2 className="font-display text-xl font-bold tracking-wide text-slate-100">
          {title}
        </h2>
      </div>

      {loading ? (
        <div className="space-y-3">
          <Skeleton className="h-14 w-full" />
          <Skeleton className="h-14 w-full" />
          <Skeleton className="h-14 w-full" />
        </div>
      ) : visible.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-10 text-slate-500">
          <Inbox size={28} />
          <p className="mt-3 text-sm">No activity yet.</p>
        </div>
      ) : (
        <div className="relative space-y-5 before:absolute before:bottom-2 before:left-[15px] before:top-2 before:w-px before:bg-slate-800">
          {visible.map((item) => {
            const meta = getActivityMeta(item.action);
            const Icon = meta.icon;

            return (
              <div key={item.id} className="relative flex items-start gap-4 pl-0">
                <div className="z-10 mt-0.5 rounded-lg border border-cyan-500/30 bg-slate-900 p-2 text-cyan-400 shadow-[0_0_16px_rgba(0,207,255,0.15)]">
                  <Icon size={16} />
                </div>

                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-3">
                    <p className="truncate text-sm font-semibold text-slate-200">
                      {meta.label}
                    </p>
                    <span className="shrink-0 font-mono text-[11px] text-slate-500">
                      {formatRelativeTime(item.created_at)}
                    </span>
                  </div>

                  {item.detail && (
                    <p className="mt-0.5 truncate text-sm text-slate-400">
                      {item.detail}
                    </p>
                  )}

                  {item.ip_address && (
                    <p className="mt-0.5 font-mono text-[11px] text-slate-500">
                      {item.ip_address}
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}