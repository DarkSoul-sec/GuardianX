import { FishSymbol, ListChecks, ShieldAlert, ShieldCheck, ShieldQuestion } from "lucide-react";

import {
  Badge,
  Button,
  Card,
  DashboardGrid,
  DataTable,
  EmptyState,
  RiskGauge,
  SkeletonCard,
  StatCard,
  TableSkeleton,
} from "@/shared/components";
import type { Column } from "@/shared/components";

import { formatDate } from "@/shared/utils/format";

import type {
  PhishingAnalysisResponse,
  PhishingCheckResult,
  PhishingRiskLevel,
} from "@/types/phishing";

type BadgeColor = "red" | "orange" | "yellow" | "green" | "gray";

function riskBadgeColor(level: PhishingRiskLevel): BadgeColor {
  switch (level) {
    case "critical":
      return "red";
    case "high":
      return "orange";
    case "medium":
      return "yellow";
    default:
      return "green";
  }
}

function scoreBadgeColor(score: number): BadgeColor {
  if (score >= 75) return "red";
  if (score >= 50) return "orange";
  if (score >= 25) return "yellow";
  return "green";
}

const columns: Column<PhishingCheckResult>[] = [
  {
    key: "check",
    title: "Check",
    render: (row) => (
      <span className="font-mono text-xs text-cyan-300">{row.check}</span>
    ),
  },
  { key: "title", title: "Indicator" },
  {
    key: "score",
    title: "Score",
    render: (row) => <Badge color={scoreBadgeColor(row.score)}>{row.score}</Badge>,
  },
  {
    key: "severity",
    title: "Severity",
    render: (row) => (
      <Badge color={scoreBadgeColor(row.score)}>{row.severity}</Badge>
    ),
  },
  { key: "reason", title: "Reason" },
];

interface Props {
  data?: PhishingAnalysisResponse;
  loading: boolean;
  error: Error | null;
  hasRequest: boolean;
  onRetry: () => void;
}

function VerdictCard({ data }: { data: PhishingAnalysisResponse }) {
  const clean = data.risk_level === "low";
  const Icon = clean ? ShieldCheck : ShieldAlert;

  return (
    <Card>
      <div className="flex flex-wrap items-center gap-6">
        <RiskGauge score={data.threat_score} label={data.risk_level} />

        <div className="min-w-0 flex-1">
          <p className="eyebrow">Phishing Verdict</p>
          <h2 className="mt-1 break-all font-mono text-xl font-bold text-white">
            {data.url}
          </h2>

          <div className="mt-3 flex flex-wrap items-center gap-2">
            <Badge color={riskBadgeColor(data.risk_level)}>
              {data.risk_level} risk
            </Badge>
            <span className="text-xs text-slate-500">
              Analyzed {formatDate(data.generated_at)}
            </span>
          </div>

          <div
            className={`mt-4 rounded-xl border p-4 text-sm ${
              clean
                ? "border-emerald-400/30 bg-emerald-500/10 text-emerald-200"
                : "border-rose-400/30 bg-rose-500/10 text-rose-200"
            }`}
          >
            <div className="flex items-center gap-2 font-semibold">
              <Icon size={18} />
              {clean
                ? "No significant phishing indicators detected."
                : "Potential phishing indicators detected."}
            </div>
            {data.ai_summary && (
              <p className="mt-2 text-slate-300">{data.ai_summary}</p>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
}

function ReasonsCard({
  reasons,
  recommendations,
}: {
  reasons: string[];
  recommendations: string[];
}) {
  return (
    <Card>
      <h3 className="mb-4 flex items-center gap-2 text-lg font-bold text-white">
        <ListChecks size={18} className="text-cyan-400" />
        Assessment
      </h3>

      <div className="grid gap-6 md:grid-cols-2">
        <div>
          <h4 className="eyebrow mb-3">Reasons</h4>
          {reasons.length > 0 ? (
            <ul className="space-y-2">
              {reasons.map((reason) => (
                <li
                  key={reason}
                  className="flex items-start gap-2 text-sm text-slate-300"
                >
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-amber-400" />
                  {reason}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-slate-500">Nothing notable found.</p>
          )}
        </div>

        <div>
          <h4 className="eyebrow mb-3">Recommendations</h4>
          {recommendations.length > 0 ? (
            <ul className="space-y-2">
              {recommendations.map((recommendation) => (
                <li
                  key={recommendation}
                  className="flex items-start gap-2 text-sm text-slate-300"
                >
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-cyan-400" />
                  {recommendation}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-slate-500">No action required.</p>
          )}
        </div>
      </div>
    </Card>
  );
}

export default function PhishingAnalysisResults({
  data,
  loading,
  error,
  hasRequest,
  onRetry,
}: Props) {
  if (loading) {
    return (
      <div className="space-y-6">
        <DashboardGrid columns={4}>
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </DashboardGrid>
        <TableSkeleton rows={6} columns={4} />
      </div>
    );
  }

  if (error) {
    return (
      <EmptyState
        title="Analysis Failed"
        description="Unable to analyze this URL. Please check the URL and try again."
        icon={<ShieldQuestion size={45} />}
        action={<Button onClick={onRetry}>Retry</Button>}
      />
    );
  }

  if (!hasRequest || !data) {
    return (
      <EmptyState
        title="No Analysis Yet"
        description="Enter a URL above to run a multi-layered phishing analysis."
        icon={<FishSymbol size={45} />}
      />
    );
  }

  const flagged = data.checks.filter((check) => check.score >= 50).length;

  return (
    <div className="space-y-6">
      <VerdictCard data={data} />

      <DashboardGrid columns={4}>
        <StatCard
          label="Threat Score"
          value={data.threat_score}
          hint="0 = clean, 100 = high risk"
          icon={<ShieldAlert size={20} />}
          accent={data.threat_score >= 50 ? "rose" : "emerald"}
        />
        <StatCard
          label="Risk Level"
          value={data.risk_level.toUpperCase()}
          hint="Overall phishing risk"
          icon={<ShieldAlert size={20} />}
          accent={data.threat_score >= 50 ? "amber" : "cyan"}
        />
        <StatCard
          label="Flags Raised"
          value={flagged}
          hint={`out of ${data.checks.length} checks`}
          icon={<ShieldCheck size={20} />}
          accent={flagged > 0 ? "amber" : "emerald"}
        />
        <StatCard
          label="Recommendations"
          value={data.recommendations.length}
          hint="Remediation actions"
          icon={<ListChecks size={20} />}
          accent="blue"
        />
      </DashboardGrid>

      <ReasonsCard
        reasons={data.reasons}
        recommendations={data.recommendations}
      />

      <div>
        <h2 className="mb-4 text-xl font-bold text-white">Detection Checks</h2>
        <DataTable
          columns={columns}
          data={data.checks}
          rowKey={(row) => row.check}
          emptyText="No checks were performed."
          ariaLabel="Phishing detection checks"
        />
      </div>
    </div>
  );
}
