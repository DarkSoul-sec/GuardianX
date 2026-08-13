import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { chartPalette } from "@/theme";
import type { EpssHistoryPoint } from "@/types/threat-intel";

interface Props {
  data: EpssHistoryPoint[];
}

export default function EpssTrendChart({ data }: Props) {
  if (data.length < 2) {
    return (
      <p className="py-16 text-center text-sm text-slate-500">
        EPSS trend available once this CVE has been scored on multiple days.
      </p>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <AreaChart data={data}>
        <defs>
          <linearGradient id="epssTrendFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={chartPalette.cyan} stopOpacity={0.35} />
            <stop offset="100%" stopColor={chartPalette.cyan} stopOpacity={0} />
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
          width={40}
          tickFormatter={(value: number) => `${Math.round(value * 100)}%`}
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
          formatter={(value) => {
            const raw = typeof value === "number" ? value : Number(value ?? 0);
            return `${(raw * 100).toFixed(1)}%`;
          }}
        />
        <Area
          type="monotone"
          dataKey="score"
          name="EPSS"
          stroke={chartPalette.cyan}
          strokeWidth={3}
          fill="url(#epssTrendFill)"
          dot={{ fill: chartPalette.cyan, r: 3 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
