import { ExternalLink, Flame, LineChart, Swords, Timer, X } from "lucide-react";

import {
  Badge,
  Button,
  Card,
  Modal,
  RiskGauge,
  Skeleton,
} from "@/shared/components";

import { formatDate } from "@/shared/utils/format";

import { useThreatIntelCve } from "@/hooks/useThreatIntel";
import type { CveSeverity } from "@/types/threat-intel";

import EpssTrendChart from "@/components/threat-intel/EpssTrendChart";

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

function ScoreBar({ value, label }: { value: number; label: string }) {
  const percent = Math.round(value * 100);
  const color = percent >= 70 ? "bg-rose-500" : percent >= 30 ? "bg-amber-500" : "bg-emerald-500";

  return (
    <div>
      <div className="flex items-center justify-between text-xs text-slate-400">
        <span>{label}</span>
        <span className="font-mono font-semibold text-white">{percent}%</span>
      </div>
      <div className="mt-1.5 h-2 overflow-hidden rounded-full bg-slate-800">
        <div
          className={`h-full rounded-full ${color}`}
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}

interface Props {
  cveId: string | null;
  onClose: () => void;
}

export default function CveDetailModal({ cveId, onClose }: Props) {
  const { data, isLoading } = useThreatIntelCve(cveId);

  return (
    <Modal open={Boolean(cveId)} onClose={onClose}>
      <div className="max-h-[85vh] overflow-y-auto p-8">
        {isLoading || !data ? (
          <div className="space-y-4 py-8">
            <Skeleton className="h-8 w-2/3" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-40 w-full" />
          </div>
        ) : (
          <div className="space-y-6">
            <div>
              <p className="eyebrow">Vulnerability Intelligence</p>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                <h2 className="font-mono text-2xl font-bold text-white">
                  {data.id}
                </h2>
                <Badge color={severityBadgeColor(data.severity)}>
                  {data.severity}
                </Badge>
                {data.exploited && (
                  <Badge color="red">
                    <Flame size={12} />
                    Actively exploited
                  </Badge>
                )}
              </div>
              <h3 className="mt-2 text-base font-semibold text-cyan-200">
                {data.title}
              </h3>

              {data.vendor && (
                <p className="mt-1 text-sm text-slate-400">
                  Affected vendor: <span className="text-slate-200">{data.vendor}</span>
                </p>
              )}
            </div>

            <div className="grid gap-6 md:grid-cols-[180px_1fr]">
              <Card>
                <div className="flex flex-col items-center gap-2">
                  <RiskGauge
                    score={Math.round((data.epss_score ?? 0) * 100)}
                    size={150}
                    label="EPSS"
                  />
                  <p className="text-center text-xs text-slate-400">
                    Exploit likelihood
                  </p>
                  {data.epss_percentile !== null &&
                    data.epss_percentile !== undefined && (
                      <p className="text-center text-xs text-slate-500">
                        {data.epss_percentile.toFixed(1)}th percentile
                      </p>
                    )}
                </div>
              </Card>

              <Card>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-xs text-slate-500">CVSS Score</p>
                      <p className="mt-1 font-mono text-2xl font-bold text-white">
                        {data.cvss_score !== null
                          ? data.cvss_score.toFixed(1)
                          : "-"}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-500">Published</p>
                      <p className="mt-1 font-mono text-sm font-semibold text-slate-200">
                        {formatDate(data.published)}
                      </p>
                    </div>
                  </div>
                  {data.epss_score !== null && (
                    <ScoreBar value={data.epss_score} label="EPSS score" />
                  )}
                </div>
              </Card>
            </div>

            {data.epss_history.length >= 2 && (
              <div>
                <h4 className="mb-3 flex items-center gap-2 eyebrow">
                  <LineChart size={14} className="text-cyan-400" />
                  EPSS Trend
                </h4>
                <Card>
                  <EpssTrendChart data={data.epss_history} />
                </Card>
              </div>
            )}

            {data.description && (
              <div>
                <h4 className="eyebrow mb-2">Description</h4>
                <p className="text-sm leading-relaxed text-slate-300">
                  {data.description}
                </p>
              </div>
            )}

            {data.attack_techniques.length > 0 && (
              <div>
                <h4 className="mb-3 flex items-center gap-2 eyebrow">
                  <Swords size={14} className="text-cyan-400" />
                  MITRE ATT&CK Techniques
                </h4>
                <div className="space-y-2">
                  {data.attack_techniques.map((technique) => (
                    <div
                      key={technique.id}
                      className="rounded-xl border border-slate-800 bg-slate-900/60 p-4"
                    >
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge color="cyan">{technique.id}</Badge>
                        <span className="text-sm font-semibold text-white">
                          {technique.name}
                        </span>
                        {technique.tactics.map((tactic) => (
                          <Badge key={tactic} color="gray">
                            {tactic}
                          </Badge>
                        ))}
                      </div>
                      {technique.description && (
                        <p className="mt-2 text-xs text-slate-400">
                          {technique.description}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {data.advisories.length > 0 && (
              <div>
                <h4 className="mb-3 flex items-center gap-2 eyebrow">
                  <Timer size={14} className="text-cyan-400" />
                  Vendor Advisories & References
                </h4>
                <ul className="space-y-2">
                  {data.advisories.map((advisory) => (
                    <li key={advisory.url}>
                      <Button asChild variant="secondary">
                        <a
                          href={advisory.url}
                          target="_blank"
                          rel="noreferrer"
                        >
                          <ExternalLink size={14} className="mr-2 inline" />
                          {advisory.source || advisory.url}
                          {advisory.tags.length > 0 && (
                            <span className="ml-2 text-xs text-slate-400">
                              · {advisory.tags.join(", ")}
                            </span>
                          )}
                        </a>
                      </Button>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div className="flex items-center justify-end gap-2 border-t border-slate-800 pt-4">
              <Button onClick={onClose} variant="secondary">
                <X size={16} className="mr-2 inline" />
                Close
              </Button>
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
}
