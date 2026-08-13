import { Link } from "react-router-dom";
import { Crosshair } from "lucide-react";

import Badge from "@/shared/components/Badge";
import Card from "@/shared/components/Card";
import { riskColor, riskLevel } from "@/theme";

import type { VulnerableAsset } from "@/types/dashboard";

const badgeColor: Record<string, "red" | "orange" | "yellow" | "green"> = {
  critical: "red",
  high: "orange",
  medium: "yellow",
  low: "green",
};

interface Props {
  assets: VulnerableAsset[];
}

export default function TopVulnerableAssetsCard({ assets }: Props) {
  const maxScore = Math.max(1, ...assets.map((asset) => asset.risk_score));

  return (
    <Card className="space-y-5">
      <div className="flex items-center gap-2">
        <div className="rounded-xl bg-cyan-500/10 p-2 text-cyan-400">
          <Crosshair size={18} />
        </div>
        <div>
          <h2 className="font-display text-xl font-bold tracking-wide text-slate-100">
            Top Vulnerable Assets
          </h2>
          <p className="text-sm text-slate-400">
            Highest risk assets by findings.
          </p>
        </div>
      </div>

      {assets.length === 0 ? (
        <p className="py-8 text-center text-sm text-slate-400">
          No assets to report.
        </p>
      ) : (
        <div className="space-y-4">
          {assets.map((asset) => {
            const color = riskColor(asset.risk_score);

            return (
              <Link
                key={asset.asset_id}
                to={`/assets/${asset.asset_id}`}
                className="block rounded-xl border border-slate-800 bg-slate-950/60 p-4 transition hover:border-slate-700 hover:bg-slate-900"
              >
                <div className="flex items-center justify-between gap-3">
                  <p className="min-w-0 truncate font-semibold text-slate-100">
                    {asset.asset_name}
                  </p>
                  <Badge color={badgeColor[riskLevel(asset.risk_score)]}>
                    {asset.risk_score}
                  </Badge>
                </div>

                <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-slate-800">
                  <div
                    className="h-full rounded-full transition-all duration-700"
                    style={{
                      width: `${(asset.risk_score / maxScore) * 100}%`,
                      backgroundColor: color,
                    }}
                  />
                </div>

                <p className="mt-2 text-xs text-slate-500">
                  {asset.total_findings} findings
                  {asset.critical_findings > 0 &&
                    ` • ${asset.critical_findings} critical`}
                </p>
              </Link>
            );
          })}
        </div>
      )}
    </Card>
  );
}
