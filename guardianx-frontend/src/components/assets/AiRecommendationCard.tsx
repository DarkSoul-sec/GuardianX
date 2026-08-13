import RecommendationCard from "@/shared/components/RecommendationCard";
import type { Recommendation } from "@/shared/components/RecommendationCard";

import type { AssetDetails } from "@/types/asset";

const SENSITIVE_PORTS = new Set([21, 22, 23, 445, 1433, 3306, 5432, 6379, 27017, 3389]);

function buildRecommendations(asset: AssetDetails): Recommendation[] {
  const recommendations: Recommendation[] = [];
  const severe = asset.critical + asset.high;

  if (severe > 0) {
    recommendations.push({
      id: "severe-findings",
      tone: "critical",
      title: `Remediate ${severe} high-severity finding${severe === 1 ? "" : "s"}`,
      detail:
        "Critical and high severity vulnerabilities are actively exploitable. Prioritize patching and apply the recommended fixes from each finding.",
    });
  }

  if (asset.internet_facing) {
    recommendations.push({
      id: "internet-facing",
      tone: "warning",
      title: "Reduce internet-facing exposure",
      detail:
        "This asset is reachable from the internet, expanding the attack surface. Restrict inbound access with network segmentation or a firewall allow-list.",
    });
  }

  const sensitive = asset.open_ports.filter((port) => SENSITIVE_PORTS.has(port));
  if (sensitive.length > 0) {
    recommendations.push({
      id: "sensitive-ports",
      tone: "warning",
      title: `Harden exposed management ports: ${sensitive.join(", ")}`,
      detail:
        "Administrative and database ports should not be exposed. Move them behind a VPN or bastion host and enforce strong authentication.",
    });
  }

  const unfingerprinted = asset.services.filter(
    (service) => service.state === "open" && !service.product
  ).length;
  if (unfingerprinted > 0) {
    recommendations.push({
      id: "fingerprinting",
      tone: "info",
      title: `Enable fingerprinting for ${unfingerprinted} service${unfingerprinted === 1 ? "" : "s"}`,
      detail:
        "Services without a detected product cannot be matched to known vulnerabilities. Run a version-detection scan to improve coverage.",
    });
  }

  if (!asset.operating_system) {
    recommendations.push({
      id: "enrichment",
      tone: "info",
      title: "Enrich asset metadata",
      detail:
        "No operating system is recorded. Complete the asset profile so the risk engine can weigh OS-specific vulnerabilities.",
    });
  }

  if (asset.recent_scans.length === 0) {
    recommendations.push({
      id: "scan-cadence",
      tone: "info",
      title: "Establish a scan cadence",
      detail:
        "No recent scans found. Schedule recurring scans to keep the asset posture up to date and detect drift.",
    });
  }

  if (asset.total_findings === 0 && asset.open_ports.length === 0) {
    recommendations.push({
      id: "healthy",
      tone: "success",
      title: "No known exposure detected",
      detail:
        "This asset currently has no open ports or recorded findings. Continue monitoring to confirm the posture stays clean.",
    });
  }

  return recommendations;
}

interface Props {
  asset: AssetDetails;
}

export default function AiRecommendationCard({ asset }: Props) {
  return (
    <RecommendationCard
      title="AI Recommendations"
      subtitle="Generated from live asset intelligence."
      recommendations={buildRecommendations(asset)}
    />
  );
}
