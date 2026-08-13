import { Database, ExternalLink, ShieldAlert, ShieldCheck } from "lucide-react";

import { Badge, Button, Card } from "@/shared/components";
import { formatDate, toTitleCase } from "@/shared/utils/format";

import type { IntelligenceReport } from "@/types/intelligence";

import { IOC_META } from "./ioc";
import { THREAT_LEVEL_META } from "./labels";

interface Props {
  report: IntelligenceReport;
}

export default function ThreatSummary({ report }: Props) {
  const VerdictIcon = report.detected ? ShieldAlert : ShieldCheck;
  const verdictColor = report.detected ? "red" : "green";
  const typeMeta = IOC_META[report.resource_type];

  return (
    <Card>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div
            className={`rounded-2xl border p-4 ${
              report.detected
                ? "border-rose-400/40 bg-rose-500/10 text-rose-300"
                : "border-emerald-400/40 bg-emerald-500/10 text-emerald-300"
            }`}
          >
            <VerdictIcon size={26} />
          </div>

          <div>
            <p className="eyebrow">Threat Intelligence · {typeMeta.label}</p>
            <h2 className="mt-1 break-all font-mono text-xl font-bold text-white">
              {report.resource}
            </h2>

            <div className="mt-3 flex flex-wrap items-center gap-2">
              <Badge color={verdictColor}>
                {report.detected ? "Detected" : "Clean"}
              </Badge>
              <Badge color={THREAT_LEVEL_META[report.threat_level].color}>
                {THREAT_LEVEL_META[report.threat_level].label}
              </Badge>
              {report.threat_category && (
                <Badge color="blue">{report.threat_category}</Badge>
              )}
              {report.from_cache && (
                <Badge color="amber">
                  <Database size={12} /> Cached 24h
                </Badge>
              )}
              {report.last_analysis && (
                <span className="text-xs text-slate-500">
                  Analyzed {formatDate(report.last_analysis)}
                </span>
              )}
            </div>
          </div>
        </div>

        <Button asChild variant="secondary">
          <a href={report.permalink} target="_blank" rel="noreferrer">
            <ExternalLink size={16} className="mr-2 inline" />
            View on VirusTotal
          </a>
        </Button>
      </div>

      <p className="mt-4 text-xs text-slate-500">
        Type detected as{" "}
        <span className="font-semibold text-cyan-300">
          {toTitleCase(report.resource_type)}
        </span>
        {" · "}
        {typeMeta.description}
      </p>
    </Card>
  );
}
