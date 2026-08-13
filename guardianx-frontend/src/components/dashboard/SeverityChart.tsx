import { ChartCard, SciFiDonut } from "@/shared/components";
import type { DonutSegment } from "@/shared/components";
import { severityChartGradients, severityOrder } from "@/theme";
import type { SeverityLevel } from "@/theme";

interface Props {
  critical: number;
  high: number;
  medium: number;
  low: number;
}

export default function SeverityChart({ critical, high, medium, low }: Props) {
  const values: Record<SeverityLevel, number> = {
    critical,
    high,
    medium,
    low,
    unknown: 0,
  };

  const data: DonutSegment[] = severityOrder
    .map((level) => ({
      name: level.charAt(0).toUpperCase() + level.slice(1),
      value: values[level],
      ...severityChartGradients[level],
    }))
    .filter((entry) => entry.value > 0);

  const total = critical + high + medium + low;

  return (
    <ChartCard title="Severity Distribution">
      {data.length === 0 ? (
        <p className="py-20 text-slate-400">No findings to display.</p>
      ) : (
        <SciFiDonut
          data={data}
          centerValue={total}
          centerLabel="Findings"
          legend
        />
      )}
    </ChartCard>
  );
}
