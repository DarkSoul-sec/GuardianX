import { useState } from "react";
import { KeyRound, ScrollText } from "lucide-react";

import ActivityTimeline from "@/components/soc/ActivityTimeline";
import { PageHeader, Skeleton } from "@/shared/components";
import { useActivity, useLoginHistory } from "@/hooks/useSoc";
import { formatRelativeTime } from "@/shared/utils/format";
import type { ActivityItem } from "@/types/soc";

type Tab = "timeline" | "logins";

export default function Activity() {
  const [tab, setTab] = useState<Tab>("timeline");

  const activity = useActivity(100);
  const logins = useLoginHistory(50);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Activity & Audit Log"
        subtitle="Full history of actions taken across the platform"
      />

      <div className="flex gap-1 rounded-xl border border-slate-800 bg-slate-900/60 p-1">
        {(
          [
            { key: "timeline", label: "Timeline", icon: ScrollText },
            { key: "logins", label: "Login History", icon: KeyRound },
          ] as const
        ).map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`flex flex-1 items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-semibold transition ${
              tab === key
                ? "bg-cyan-500/15 text-cyan-300 shadow-[inset_0_0_20px_rgba(0,207,255,0.12)]"
                : "text-slate-400 hover:text-cyan-200"
            }`}
          >
            <Icon size={16} />
            {label}
          </button>
        ))}
      </div>

      {tab === "timeline" ? (
        activity.isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
          </div>
        ) : (
          <ActivityTimeline
            title="All activity"
            items={activity.data?.items ?? []}
            limit={100}
          />
        )
      ) : logins.isLoading ? (
        <div className="space-y-3">
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-16 w-full" />
        </div>
      ) : (
        <div className="panel panel-hover rounded-2xl p-6">
          <h2 className="mb-5 font-display text-xl font-bold tracking-wide text-slate-100">
            Recent logins
          </h2>
          <div className="space-y-3">
            {(logins.data?.items ?? []).map((login: ActivityItem) => (
              <div
                key={login.id}
                className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-900/40 px-4 py-3"
              >
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold text-slate-200">
                    {login.detail ?? "Signed in"}
                  </p>
                  {login.ip_address && (
                    <p className="mt-0.5 font-mono text-[11px] text-slate-500">
                      {login.ip_address}
                    </p>
                  )}
                </div>
                <span className="shrink-0 font-mono text-xs text-slate-400">
                  {formatRelativeTime(login.created_at)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}