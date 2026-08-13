import { Pie, PieChart, Cell, ResponsiveContainer, Tooltip } from "recharts";

import ChartCard from "@/shared/components/ChartCard";
import { chartPalette } from "@/theme";
import { toTitleCase } from "@/shared/utils/format";

import type { AssetDistributionItem } from "@/types/dashboard";

interface Props {
  data: AssetDistributionItem[];
}

const palette = [
  chartPalette.cyan,
  chartPalette.blue,
  chartPalette.purple,
  chartPalette.emerald,
  chartPalette.amber,
  chartPalette.rose,
  "#64748b",
];

export default function AssetDistributionChart({ data }: Props) {
  const total = data.reduce((sum, entry) => sum + entry.count, 0);

  const items = data.map((entry, index) => ({
    ...entry,
    color: palette[index % palette.length],
  }));

  return (
    <ChartCard
      title="Asset Distribution"
      subtitle={`${total} assets by type`}
    >
      {items.length === 0 ? (
        <p className="py-20 text-slate-400">No assets to display.</p>
      ) : (
        <div className="flex w-full flex-col items-center justify-center gap-6 sm:flex-row">
          <div className="relative h-52 w-52 shrink-0">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={items}
                  dataKey="count"
                  nameKey="type"
                  innerRadius={62}
                  outerRadius={92}
                  paddingAngle={2}
                  stroke="rgba(3, 6, 22, 0.9)"
                  strokeWidth={2}
                >
                  {items.map((entry) => (
                    <Cell key={entry.type} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    background: "#0f172a",
                    border: "1px solid #334155",
                    borderRadius: 12,
                  }}
                  labelStyle={{ color: "#94a3b8" }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
              <p className="font-mono text-3xl font-bold text-white">
                {total}
              </p>
              <p className="text-xs uppercase tracking-wider text-slate-500">
                Assets
              </p>
            </div>
          </div>

          <ul className="w-full space-y-2.5 sm:max-w-[220px]">
            {items.map((entry) => (
              <li key={entry.type} className="flex items-center gap-2.5">
                <span
                  className="h-2.5 w-2.5 shrink-0 rounded-full shadow-[0_0_8px_currentColor]"
                  style={{ backgroundColor: entry.color, color: entry.color }}
                />
                <span className="min-w-0 flex-1 truncate text-sm text-slate-300">
                  {toTitleCase(entry.type)}
                </span>
                <span className="font-mono text-xs text-slate-500">
                  {total > 0 ? Math.round((entry.count / total) * 100) : 0}%
                </span>
                <span className="font-mono text-sm font-semibold text-slate-100">
                  {entry.count}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </ChartCard>
  );
}
