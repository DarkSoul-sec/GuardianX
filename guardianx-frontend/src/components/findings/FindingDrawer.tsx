import { History } from "lucide-react";

import { useFinding, useFindingActivities, useFindingIntelligence } from "@/hooks/useFindings";
import VulnerabilityIntelligenceCards from "@/components/findings/VulnerabilityIntelligenceCards";
import FindingTriageForm from "@/components/findings/FindingTriageForm";
import VirusTotalAnalyzeSection from "@/components/virustotal/VirusTotalAnalyzeSection";
import {
  CvssBadge,
  Drawer,
  SeverityBadge,
  Skeleton,
  StatusBadge,
} from "@/shared/components";

interface Props {
  id: number | null;
  onClose: () => void;
}

const ACTIVITY_LABELS: Record<string, string> = {
  status: "Status changed",
  assignee: "Assignee changed",
  notes: "Notes updated",
  due_date: "Due date changed",
};

export default function FindingDrawer({ id, onClose }: Props) {
  const { data, isLoading, error } = useFinding(id ?? 0);
  const intelligence = useFindingIntelligence(id ?? 0, Boolean(data?.cve));
  const { data: activities = [] } = useFindingActivities(id ?? 0);

  if (!id) return null;

  return (
    <Drawer open={!!id} onClose={onClose} titleId="finding-drawer-title">
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h2 id="finding-drawer-title" className="text-3xl font-bold">Finding Details</h2>
            <p className="mt-1 text-slate-400">Vulnerability Information</p>
          </div>

          <button
            onClick={onClose}
            className="rounded-lg bg-slate-800 px-4 py-2 transition hover:bg-slate-700"
          >
            Close
          </button>
        </div>

        {isLoading && (
          <div className="space-y-4">
            <Skeleton className="h-10 w-2/3" />
            <Skeleton className="h-40 w-full" />
            <Skeleton className="h-40 w-full" />
          </div>
        )}

        {error && (
          <div className="py-20 text-center text-red-400">
            Failed to load finding.
          </div>
        )}

        {data && (
          <div className="space-y-8">
            <div>
              <h1 className="text-2xl font-bold">{data.cve ?? data.title}</h1>
              <p className="mt-2 text-slate-400">{data.title}</p>

              {data.cve && (
                <a
                  href={`https://nvd.nist.gov/vuln/detail/${data.cve}`}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-5 inline-block rounded-lg bg-cyan-600 px-5 py-2 font-semibold transition hover:bg-cyan-500"
                >
                  View on NVD
                </a>
              )}
            </div>

            <div className="flex gap-3">
              <SeverityBadge severity={data.severity} />
              <StatusBadge status={data.status} />
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">
              <h3 className="mb-4 text-xl font-bold">Triage</h3>
              <FindingTriageForm finding={data} />
            </div>

            {data.cve && (
              <VulnerabilityIntelligenceCards
                response={intelligence.data}
                loading={intelligence.isLoading}
              />
            )}

            <div className="grid grid-cols-2 gap-5">
              <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
                <p className="text-sm text-slate-400">CVSS Score</p>
                <div className="mt-3">
                  <CvssBadge score={data.cvss} />
                </div>
              </div>

              <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
                <p className="text-sm text-slate-400">Asset</p>
                <h3 className="mt-3 text-lg font-semibold">
                  {data.affected_asset ?? "-"}
                </h3>
              </div>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">
              <h3 className="mb-4 text-xl font-bold">Description</h3>
              <p className="leading-7 text-slate-300">
                {data.description ?? "No description available."}
              </p>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">
              <h3 className="mb-4 text-xl font-bold">Recommendation</h3>
              <p className="leading-7 text-slate-300">
                {data.recommendation ?? "No recommendation available."}
              </p>
            </div>

            <VirusTotalAnalyzeSection
              text={[
                data.title,
                data.description ?? "",
                data.affected_asset ?? "",
                data.affected_service ?? "",
              ].join(" ")}
            />

            <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">
              <h3 className="mb-5 text-xl font-bold">Technical Information</h3>

              <div className="space-y-3">
                <div className="flex justify-between border-b border-slate-800 pb-3">
                  <span className="text-slate-400">CVE</span>
                  <span>{data.cve ?? "-"}</span>
                </div>
                <div className="flex justify-between border-b border-slate-800 pb-3">
                  <span className="text-slate-400">Severity</span>
                  <span>{data.severity}</span>
                </div>
                <div className="flex justify-between border-b border-slate-800 pb-3">
                  <span className="text-slate-400">Status</span>
                  <span>{data.status}</span>
                </div>
                <div className="flex justify-between border-b border-slate-800 pb-3">
                  <span className="text-slate-400">Assignee</span>
                  <span>{data.assigned_to_name ?? "Unassigned"}</span>
                </div>
                <div className="flex justify-between border-b border-slate-800 pb-3">
                  <span className="text-slate-400">Due Date</span>
                  <span>
                    {data.due_date
                      ? new Date(data.due_date).toLocaleDateString()
                      : "-"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Asset</span>
                  <span>{data.affected_asset ?? "-"}</span>
                </div>
              </div>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">
              <h3 className="mb-4 flex items-center gap-2 text-xl font-bold">
                <History size={18} />
                Activity Log
              </h3>

              {activities.length === 0 ? (
                <p className="text-sm text-slate-500">
                  No activity recorded yet.
                </p>
              ) : (
                <ul className="space-y-4">
                  {activities.map((activity) => (
                    <li
                      key={activity.id}
                      className="border-l-2 border-cyan-500 pl-4"
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <p className="font-semibold text-slate-200">
                          {ACTIVITY_LABELS[activity.action] ?? activity.action}
                        </p>
                        <span className="text-xs text-slate-500">
                          {new Date(activity.created_at).toLocaleString()}
                        </span>
                      </div>
                      <p className="mt-1 text-sm text-slate-400">
                        {activity.username ?? "System"} ·{" "}
                        {activity.old_value ?? "—"} →{" "}
                        {activity.new_value ?? "—"}
                      </p>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        )}
    </Drawer>
  );
}
