import { ShieldAlert } from "lucide-react";

import Badge from "@/shared/components/Badge";
import Card from "@/shared/components/Card";
import CvssBadge from "@/shared/components/CvssBadge";
import SeverityBadge from "@/shared/components/SeverityBadge";
import { severityChartColors } from "@/theme";
import { truncate } from "@/shared/utils/format";

import type { TopVulnerability } from "@/types/dashboard";

interface Props {
  vulnerabilities: TopVulnerability[];
}

const statusColor: Record<string, "red" | "yellow" | "green" | "gray"> = {
  OPEN: "red",
  "IN_PROGRESS": "yellow",
  RESOLVED: "green",
  "FALSE_POSITIVE": "gray",
  "ACCEPTED_RISK": "gray",
};

const barColor: Record<string, string> = {
  CRITICAL: severityChartColors.critical,
  HIGH: severityChartColors.high,
  MEDIUM: severityChartColors.medium,
  LOW: severityChartColors.low,
};

export default function TopVulnerabilitiesCard({ vulnerabilities }: Props) {
  const maxCvss = Math.max(
    1,
    ...vulnerabilities.map((v) => v.cvss ?? 0)
  );

  return (
    <Card className="space-y-5">
      <div className="flex items-center gap-3">
        <div className="rounded-xl bg-rose-500/10 p-2 text-rose-400">
          <ShieldAlert size={18} />
        </div>
        <div>
          <h2 className="text-xl font-bold">Top Vulnerabilities</h2>
          <p className="text-sm text-slate-400">
            Highest CVSS findings across the estate.
          </p>
        </div>
      </div>

      {vulnerabilities.length === 0 ? (
        <p className="py-8 text-center text-sm text-slate-400">
          No vulnerabilities to report.
        </p>
      ) : (
        <div className="space-y-4">
          {vulnerabilities.map((vuln, index) => {
            const color =
              barColor[vuln.severity] ??
              severityChartColors.unknown;

            return (
              <div
                key={`${vuln.cve ?? vuln.title}-${index}`}
                className="rounded-xl border border-slate-800 bg-slate-950/60 p-4 transition hover:border-slate-700 hover:bg-slate-900"
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="flex min-w-0 items-center gap-2.5">
                    <span className="font-mono text-xs text-slate-600">
                      {String(index + 1).padStart(2, "0")}
                    </span>
                    <p className="min-w-0 truncate font-semibold text-slate-100">
                      {vuln.cve
                        ? `${vuln.cve} — ${truncate(vuln.title, 28)}`
                        : truncate(vuln.title, 40)}
                    </p>
                  </div>
                  <div className="flex shrink-0 items-center gap-1.5">
                    <CvssBadge score={vuln.cvss} />
                    <SeverityBadge severity={vuln.severity} />
                  </div>
                </div>

                <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-slate-800">
                  <div
                    className="h-full rounded-full transition-all duration-700"
                    style={{
                      width: `${((vuln.cvss ?? 0) / maxCvss) * 100}%`,
                      backgroundColor: color,
                    }}
                  />
                </div>

                <div className="mt-2 flex items-center justify-between gap-3">
                  <p className="min-w-0 truncate text-xs text-slate-500">
                    {vuln.asset}
                  </p>
                  <Badge
                    color={statusColor[vuln.status] ?? "gray"}
                    className="px-2 py-0 text-[10px]"
                  >
                    {vuln.status.replace("_", " ")}
                  </Badge>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </Card>
  );
}
