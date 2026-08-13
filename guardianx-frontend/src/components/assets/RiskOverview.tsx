import { Swords } from "lucide-react";

import SeverityChart from "@/components/dashboard/SeverityChart";
import FindingsSummary from "@/components/assets/FindingsSummary";

import {
  Card,
  DashboardGrid,
  ExposureLevelCard,
  RiskGauge,
  SecurityScoreCard,
} from "@/shared/components";
import { riskLevel } from "@/theme";

import type { AssetDetails } from "@/types/asset";

interface Props {
  asset: AssetDetails;
}

export default function RiskOverview({ asset }: Props) {
  return (
    <DashboardGrid columns={5}>
      <SecurityScoreCard score={asset.security_score} />

      <Card className="flex flex-col items-center justify-center">
        <h2 className="mb-5 self-start text-xl font-bold">Risk Score</h2>
        <RiskGauge score={asset.risk_score} label={riskLevel(asset.risk_score).toUpperCase()} />
        <div className="mt-4 flex items-center gap-2 text-sm text-slate-400">
          <Swords size={14} />
          <span>
            Attack surface:{" "}
            <span className="font-mono text-slate-200">
              {asset.attack_surface_score}
            </span>
          </span>
        </div>
      </Card>

      <ExposureLevelCard
        score={asset.attack_surface_score}
        internetFacing={asset.internet_facing}
      />

      <SeverityChart
        critical={asset.critical}
        high={asset.high}
        medium={asset.medium}
        low={asset.low}
      />

      <FindingsSummary
        critical={asset.critical}
        high={asset.high}
        medium={asset.medium}
        low={asset.low}
        total={asset.total_findings}
      />
    </DashboardGrid>
  );
}
