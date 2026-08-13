import RecommendationCard from "@/shared/components/RecommendationCard";
import type { Recommendation } from "@/shared/components/RecommendationCard";

import type { DashboardOverview } from "@/types/dashboard";

function buildRecommendations(data: DashboardOverview): Recommendation[] {
  const recommendations: Recommendation[] = [];
  const severe = data.critical_findings + data.high_findings;

  if (severe > 0) {
    recommendations.push({
      id: "severe-findings",
      tone: "critical",
      title: `Remediate ${severe} critical or high severity findings`,
      detail:
        `${data.critical_findings} critical and ${data.high_findings} high severity vulnerabilities are active across the estate. Prioritize patching in order of severity and exploitability.`,
    });
  }

  if (data.risk_score >= 50) {
    recommendations.push({
      id: "risk-posture",
      tone: "warning",
      title: `Overall risk posture elevated (${data.risk_score}/100)`,
      detail:
        "The aggregated risk score exceeds the healthy threshold. Focus remediation on the top vulnerable assets to bring the posture back under control.",
    });
  }

  if (data.open_ports > 0) {
    recommendations.push({
      id: "attack-surface",
      tone: "warning",
      title: `Reduce exposed attack surface (${data.open_ports} open ports)`,
      detail:
        `${data.open_ports} open ports and ${data.total_services} running services are exposed. Close unused ports and apply host-based firewalls to minimize reachability.`,
    });
  }

  if (data.completed_scans === 0) {
    recommendations.push({
      id: "scan-cadence",
      tone: "info",
      title: "Establish a scan cadence",
      detail:
        "No completed scans detected. Run coverage scans across all assets to establish a security baseline before assessing risk.",
    });
  }

  const recentGrowth =
    data.asset_growth.length >= 2
      ? data.asset_growth[data.asset_growth.length - 1].count -
        data.asset_growth[data.asset_growth.length - 2].count
      : 0;

  if (recentGrowth > 0) {
    recommendations.push({
      id: "asset-onboarding",
      tone: "info",
      title: `${recentGrowth} new asset${recentGrowth === 1 ? "" : "s"} onboarded recently`,
      detail:
        "Newly discovered assets expand the attack surface. Confirm each asset is registered, assigned an owner, and included in the scan schedule.",
    });
  }

  if (data.total_findings === 0 && data.open_ports === 0) {
    recommendations.push({
      id: "healthy",
      tone: "success",
      title: "Healthy security posture",
      detail:
        "No known findings or exposed ports detected. Continue monitoring and regular scanning to sustain this posture.",
    });
  }

  return recommendations;
}

interface Props {
  data: DashboardOverview;
}

export default function DashboardRecommendations({ data }: Props) {
  return (
    <RecommendationCard
      title="AI Recommendations"
      subtitle="Generated from live estate intelligence."
      recommendations={buildRecommendations(data)}
    />
  );
}
