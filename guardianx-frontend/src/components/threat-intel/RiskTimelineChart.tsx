import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import ChartCard from "@/shared/components/ChartCard";
import type { RiskTimelinePoint } from "@/types/threat-intel";

interface Props {
  data?: RiskTimelinePoint[];
  loading?: boolean;
}

export default function RiskTimelineChart({ data, loading }: Props) {
  const chartData = (data ?? []).map((point) => ({
    ...point,
    avg_epss_percent: Math.round((point.avg_epss ?? 0) * 100),
  }));

  return (
    <ChartCard
      title="Risk Timeline"
      subtitle="Daily published CVEs and average exploit likelihood (EPSS)"
      loading={loading}
    >
      {chartData.length === 0 ? (
        <p className="py-20 text-slate-400">No timeline data yet.</p>
      ) : (
        <ResponsiveContainer width="100%" height={260}>
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="cveFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#00cfff" stopOpacity={0.35} />
                <stop offset="100%" stopColor="#00cfff" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
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
              domain={[0, 100]}
              width={32}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip
              contentStyle={{
                background: "#0f172a",
                border: "1px solid #334155",
                borderRadius: 12,
              }}
              labelStyle={{ color: "#94a3b8" }}
            />
            <Area
              type="monotone"
              dataKey="published_count"
              stroke="#00cfff"
              strokeWidth={3}
              fill="url(#cveFill)"
              dot={{ fill: "#00cfff", r: 3 }}
              activeDot={{ r: 5 }}
            />
            <Line
              type="monotone"
              dataKey="avg_epss_percent"
              stroke="#8b5cf6"
              strokeWidth={2}
              dot={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </ChartCard>
  );
}
