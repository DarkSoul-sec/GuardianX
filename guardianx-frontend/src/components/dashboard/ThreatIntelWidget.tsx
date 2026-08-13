import { Link } from "react-router-dom";
import { ArrowUpRight, Crosshair, Flame } from "lucide-react";

import Badge from "@/shared/components/Badge";
import Card from "@/shared/components/Card";
import { useThreatIntelTrending } from "@/hooks/useThreatIntel";
import { truncate } from "@/shared/utils/format";

import type { CveSeverity } from "@/types/threat-intel";

type BadgeColor = "red" | "orange" | "yellow" | "green" | "gray";

function severityBadgeColor(severity: CveSeverity): BadgeColor {
  switch (severity) {
    case "CRITICAL":
      return "red";
    case "HIGH":
      return "orange";
    case "MEDIUM":
      return "yellow";
    case "LOW":
      return "green";
    default:
      return "gray";
  }
}

function epssTone(score: number | null): string {
  if (score === null) return "text-slate-400";
  if (score >= 0.5) return "text-rose-300";
  if (score >= 0.3) return "text-amber-300";
  return "text-slate-300";
}

export default function ThreatIntelWidget() {
  const { data, isLoading, error } = useThreatIntelTrending(7, 5);

  const items = data?.items ?? [];

  return (
    <Card className="flex flex-col space-y-5">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-purple-500/10 p-2 text-purple-400">
            <Crosshair size={18} />
          </div>
          <div>
            <h2 className="text-xl font-bold">Threat Intelligence</h2>
            <p className="text-sm text-slate-400">
              Trending CVEs from NVD · CISA KEV · EPSS.
            </p>
          </div>
        </div>
        <Link
          to="/threat-intel"
          className="flex shrink-0 items-center gap-1 text-sm font-semibold text-cyan-400 transition hover:text-cyan-300"
        >
          Explore
          <ArrowUpRight size={15} />
        </Link>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, index) => (
            <div
              key={index}
              className="h-14 animate-pulse rounded-xl bg-slate-900"
            />
          ))}
        </div>
      ) : error || items.length === 0 ? (
        <p className="flex-1 py-8 text-center text-sm text-slate-400">
          {error
            ? "Threat intelligence feed is unavailable."
            : "No trending CVEs in the last 7 days."}
        </p>
      ) : (
        <div className="flex-1 space-y-3">
          {items.map((cve) => (
            <Link
              key={cve.id}
              to="/threat-intel"
              className="block rounded-xl border border-slate-800 bg-slate-950/60 p-3.5 transition hover:border-cyan-700/60 hover:bg-slate-900"
            >
              <div className="flex items-center justify-between gap-3">
                <div className="flex min-w-0 items-center gap-2.5">
                  <span className="font-mono text-sm font-bold text-cyan-300">
                    {cve.id}
                  </span>
                  {cve.exploited && (
                    <Badge color="red" className="px-2 py-0 text-[10px]">
                      <Flame size={11} />
                      KEV
                    </Badge>
                  )}
                </div>
                <div className="flex shrink-0 items-center gap-1.5">
                  <Badge
                    color={severityBadgeColor(cve.severity)}
                    className="px-2 py-0 text-[10px]"
                  >
                    {cve.severity}
                  </Badge>
                </div>
              </div>

              <p className="mt-1.5 line-clamp-1 text-sm text-slate-300">
                {truncate(cve.title, 72)}
              </p>

              <div className="mt-2 flex items-center gap-3 text-xs">
                <span className={epssTone(cve.epss_score)}>
                  EPSS{" "}
                  {cve.epss_score === null
                    ? "-"
                    : `${Math.round(cve.epss_score * 100)}%`}
                </span>
                <span className="text-slate-500">
                  {cve.vendor ?? "Unknown vendor"}
                </span>
                <span className="ml-auto font-mono text-slate-500">
                  {cve.cvss_score === null
                    ? "-"
                    : cve.cvss_score.toFixed(1)}
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </Card>
  );
}
