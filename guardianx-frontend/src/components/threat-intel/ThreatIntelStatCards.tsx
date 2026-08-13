import { Flame, Radar, ShieldAlert, TrendingUp } from "lucide-react";

import { DashboardGrid, SkeletonCard, StatCard } from "@/shared/components";
import type { ThreatIntelStats } from "@/types/threat-intel";

interface Props {
  stats?: ThreatIntelStats;
  loading?: boolean;
}

export default function ThreatIntelStatCards({ stats, loading }: Props) {
  if (loading || !stats) {
    return (
      <DashboardGrid columns={4}>
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
      </DashboardGrid>
    );
  }

  const avgEpssPercent = Math.round(stats.avg_epss * 100);

  return (
    <DashboardGrid columns={4}>
      <StatCard
        label="Trending CVEs"
        value={stats.total_cves}
        hint="In the analysis window"
        icon={<Radar size={20} />}
        accent="cyan"
      />
      <StatCard
        label="Actively Exploited"
        value={stats.exploited_count}
        hint="Listed in the CISA KEV catalog"
        icon={<Flame size={20} />}
        accent={stats.exploited_count > 0 ? "rose" : "emerald"}
      />
      <StatCard
        label="Avg Exploit Likelihood"
        value={avgEpssPercent}
        suffix="%"
        hint="Mean EPSS score across recent CVEs"
        icon={<TrendingUp size={20} />}
        accent={avgEpssPercent >= 30 ? "amber" : "cyan"}
      />
      <StatCard
        label="Critical CVEs"
        value={stats.critical}
        hint={`${stats.high} high · ${stats.medium} medium · ${stats.low} low`}
        icon={<ShieldAlert size={20} />}
        accent={stats.critical > 0 ? "rose" : "blue"}
      />
    </DashboardGrid>
  );
}
