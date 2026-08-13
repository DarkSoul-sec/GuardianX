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
import { chartPalette } from "@/theme";
import type { AssetGrowthPoint } from "@/types/dashboard";

interface Props {
  data: AssetGrowthPoint[];
}

export default function AssetGrowthChart({ data }: Props) {
  const latest = data.length > 0 ? data[data.length - 1].count : 0;

  return (
    <ChartCard
      title="Asset Growth"
      subtitle={`${latest} monitored assets, 14-day view`}
    >
      <ResponsiveContainer width="100%" height={260}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id="growthFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={chartPalette.blue} stopOpacity={0.35} />
              <stop offset="100%" stopColor={chartPalette.blue} stopOpacity={0} />
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
            dataKey="count"
            name="Assets"
            stroke={chartPalette.blue}
            strokeWidth={3}
            fill="url(#growthFill)"
            dot={{ fill: chartPalette.blue, r: 3 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}
