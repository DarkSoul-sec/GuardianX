import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import ChartCard from "@/shared/components/ChartCard";
import { riskColor, riskLevel } from "@/theme";
import type { RiskTrendPoint } from "@/types/dashboard";

interface Props {
  data: RiskTrendPoint[];
  currentScore: number;
}

export default function RiskChart({ data, currentScore }: Props) {
  const color = riskColor(currentScore);
  const last =
    data.length > 0 ? data[data.length - 1].score : currentScore;
  const trend = last > currentScore ? "rising" : last < currentScore ? "falling" : "stable";

  return (
    <ChartCard
      title="Risk Trend"
      subtitle={`14-day posture • ${riskLevel(currentScore).toUpperCase()} • ${trend}`}
    >
      <ResponsiveContainer width="100%" height={260}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id="riskFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.35} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
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
            dataKey="score"
            stroke={color}
            strokeWidth={3}
            fill="url(#riskFill)"
            dot={{ fill: color, r: 3 }}
            activeDot={{ r: 5 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}
