import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import ChartCard from "@/shared/components/ChartCard";
import type { ScanHealth } from "@/types/soc";

interface Props {
  data: ScanHealth | undefined;
  loading?: boolean;
}

export default function ScanHealthChart({ data, loading }: Props) {
  return (
    <ChartCard
      title="Scan Health"
      subtitle="Daily completed vs failed scans"
      loading={loading}
    >
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data?.trend ?? []}>
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
            width={30}
            allowDecimals={false}
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
            cursor={{ fill: "rgba(148,163,184,0.08)" }}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Bar dataKey="completed" fill="#34d399" radius={[3, 3, 0, 0]} />
          <Bar dataKey="failed" fill="#f87171" radius={[3, 3, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}