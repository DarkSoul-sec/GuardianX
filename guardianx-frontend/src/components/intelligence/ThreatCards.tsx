import {
  CalendarDays,
  CalendarClock,
  Flag,
  Gauge,
  Globe,
  Network,
  Scale,
  ShieldAlert,
  ShieldCheck,
  ShieldQuestion,
  Vote,
} from "lucide-react";

import { DashboardGrid, RiskGauge, StatCard } from "@/shared/components";
import { formatDate, formatNumber } from "@/shared/utils/format";

import type { IntelligenceReport } from "@/types/intelligence";

import { THREAT_LEVEL_META } from "./labels";

interface Props {
  report: IntelligenceReport;
}

export default function ThreatCards({ report }: Props) {
  return (
    <div className="space-y-6">
      <DashboardGrid columns={4}>
        <div className="panel panel-hover flex items-center justify-center p-6">
          <RiskGauge score={report.risk_score} size={150} label="Risk Score" />
        </div>

        <StatCard
          label="Threat Level"
          value={THREAT_LEVEL_META[report.threat_level].label}
          icon={<ShieldAlert size={20} />}
          accent={
            report.threat_level === "critical"
              ? "rose"
              : report.threat_level === "high"
                ? "amber"
                : report.threat_level === "medium"
                  ? "blue"
                  : "emerald"
          }
          hint="Derived from vendor verdicts, reputation and community votes"
        />
        <StatCard
          label="Reputation Score"
          value={report.reputation}
          icon={<Gauge size={20} />}
          accent={report.reputation < 0 ? "rose" : "emerald"}
          hint="VirusTotal reputation (negative = risky)"
        />
        <StatCard
          label="Detection Ratio"
          value={report.detection_ratio}
          icon={<Scale size={20} />}
          accent={report.detected ? "rose" : "emerald"}
          hint={`${report.total} engines analyzed`}
        />
      </DashboardGrid>

      <DashboardGrid columns={4}>
        <StatCard
          label="Last Analysis"
          value={formatDate(report.last_analysis)}
          icon={<CalendarClock size={20} />}
          accent="cyan"
          hint="Most recent vendor analysis"
        />
        <StatCard
          label="Country"
          value={report.country ?? "-"}
          icon={<Flag size={20} />}
          accent="blue"
          hint="Geolocation of the indicator"
        />
        <StatCard
          label="ASN"
          value={report.asn ?? "-"}
          icon={<Network size={20} />}
          accent="cyan"
          hint={report.as_owner ?? "Autonomous system"}
        />
        <StatCard
          label="Registrar"
          value={report.registrar ?? "-"}
          icon={<Globe size={20} />}
          accent="blue"
          hint="Registration authority"
        />
      </DashboardGrid>

      <DashboardGrid columns={4}>
        <StatCard
          label="Creation Date"
          value={formatDate(report.creation_date)}
          icon={<CalendarDays size={20} />}
          accent="cyan"
          hint="WHOIS / file creation date"
        />
        <StatCard
          label="Community Votes"
          value={`${report.community_votes.malicious} / ${report.community_votes.harmless}`}
          icon={<Vote size={20} />}
          accent={report.community_votes.malicious > 0 ? "rose" : "emerald"}
          hint="Malicious / harmless community votes"
        />
        <StatCard
          label="Malicious Vendors"
          value={report.malicious}
          icon={<ShieldAlert size={20} />}
          accent={report.malicious > 0 ? "rose" : "emerald"}
          hint={`${report.suspicious} suspicious engines`}
        />
        <StatCard
          label="Harmless Vendors"
          value={report.harmless}
          icon={<ShieldCheck size={20} />}
          accent="emerald"
          hint={`${report.undetected} undetected engines`}
        />
      </DashboardGrid>

      <DashboardGrid columns={4}>
        <StatCard
          label="Undetected Vendors"
          value={report.undetected}
          icon={<ShieldQuestion size={20} />}
          accent="blue"
          hint="Engines with no verdict"
        />
        <StatCard
          label="Suspicious Vendors"
          value={report.suspicious}
          icon={<ShieldQuestion size={20} />}
          accent="amber"
          hint="Engines flagging as suspicious"
        />
        <StatCard
          label="Submissions"
          value={formatNumber(report.submission_count)}
          icon={<Vote size={20} />}
          accent="cyan"
          hint="Times reported to the provider"
        />
        <StatCard
          label="First Seen"
          value={formatDate(report.first_seen)}
          icon={<CalendarClock size={20} />}
          accent="blue"
          hint="First observation by the provider"
        />
      </DashboardGrid>
    </div>
  );
}
