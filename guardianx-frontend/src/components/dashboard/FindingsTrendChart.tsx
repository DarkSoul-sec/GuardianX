import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Legend,
} from "recharts";

import ChartCard from "@/shared/components/ChartCard";
import { severityChartColors } from "@/theme";

import type { FindingsTrendPoint } from "@/types/dashboard";

interface Props {
  data: FindingsTrendPoint[];
}

export default function FindingsTrendChart({ data }: Props) {
  const total = data.reduce(
    (sum, point) =>
      sum + point.critical + point.high + point.medium + point.low,
    0
  );

  const legendFormatter = (value: string) => (
    <span className="text-xs capitalize text-slate-300">{value}</span>
  );

  return (
    <ChartCard
      title="Findings Trend"
      subtitle={`${total} findings detected over 14 days`}
    >
      {total === 0 ? (
        <p className="py-20 text-slate-400">No findings to display.</p>
      ) : (
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={data} barCategoryGap="22%">
            <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" vertical={false} />
            <XAxis
              dataKey="date"
              stroke="#64748b"
              tick={{ fontSize: 11 }}
              tickFormatter={(value: string) => value.slice(5)}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              stroke="#64748b"
              tick={{ fontSize: 11 }}
              allowDecimals={false}
              width={32}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip
              cursor={{ fill: "rgba(139, 160, 200, 0.08)" }}
              contentStyle={{
                background: "#0f172a",
                border: "1px solid #334155",
                borderRadius: 12,
              }}
              labelStyle={{ color: "#94a3b8" }}
            />
            <Legend
              verticalAlign="bottom"
              height={28}
              iconType="circle"
              iconSize={8}
              formatter={legendFormatter}
            />
            <Bar
              dataKey="critical"
              stackId="severity"
              fill={severityChartColors.critical}
              radius={[0, 0, 0, 0]}
            />
            <Bar
              dataKey="high"
              stackId="severity"
              fill={severityChartColors.high}
            />
            <Bar
              dataKey="medium"
              stackId="severity"
              fill={severityChartColors.medium}
            />
            <Bar
              dataKey="low"
              stackId="severity"
              fill={severityChartColors.low}
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      )}
    </ChartCard>
  );
}
