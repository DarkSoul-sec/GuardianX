import { ChartCard, SciFiDonut } from "@/shared/components";
import type { DonutSegment } from "@/shared/components";
import { severityChartGradients, severityOrder } from "@/theme";
import type { SeverityLevel } from "@/theme";

import type { SeverityCount } from "@/types/threat-intel";

interface Props {
  data?: SeverityCount[];
  loading?: boolean;
}

export default function SeverityDistributionChart({ data, loading }: Props) {
  const counts: Record<SeverityLevel, number> = {
    critical: 0,
    high: 0,
    medium: 0,
    low: 0,
    unknown: 0,
  };

  for (const entry of data ?? []) {
    const level = entry.severity.toLowerCase() as SeverityLevel;
    if (level in counts) {
      counts[level] += entry.count;
    } else {
      counts.unknown += entry.count;
    }
  }

  const chartData: DonutSegment[] = severityOrder
    .map((level) => ({
      name: level.charAt(0).toUpperCase() + level.slice(1),
      value: counts[level],
      ...severityChartGradients[level],
    }))
    .filter((entry) => entry.value > 0);

  const total = Object.values(counts).reduce((sum, count) => sum + count, 0);

  return (
    <ChartCard
      title="Severity Distribution"
      subtitle="Recent CVEs by CVSS severity"
      loading={loading}
    >
      {chartData.length === 0 ? (
        <p className="py-20 text-slate-400">No CVE data to display.</p>
      ) : (
        <SciFiDonut
          data={chartData}
          centerValue={total}
          centerLabel="CVEs"
          legend
        />
      )}
    </ChartCard>
  );
}
