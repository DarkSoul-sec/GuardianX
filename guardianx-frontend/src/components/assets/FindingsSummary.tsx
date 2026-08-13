import { Activity } from "lucide-react";

import Card from "@/shared/components/Card";
import { cn } from "@/shared/utils/cn";
import { severityColors } from "@/theme";

interface SeverityRow {
  key: "critical" | "high" | "medium" | "low";
  label: string;
  count: number;
}

interface Props {
  critical: number;
  high: number;
  medium: number;
  low: number;
  total: number;
}

const rows: SeverityRow[] = [
  { key: "critical", label: "Critical", count: 0 },
  { key: "high", label: "High", count: 0 },
  { key: "medium", label: "Medium", count: 0 },
  { key: "low", label: "Low", count: 0 },
];

export default function FindingsSummary({ critical, high, medium, low, total }: Props) {
  const counts: Record<SeverityRow["key"], number> = {
    critical,
    high,
    medium,
    low,
  };
  const max = Math.max(total, 1);

  return (
    <Card className="flex flex-col">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">Findings Summary</h2>
        <div className="rounded-xl bg-cyan-500/10 p-2 text-cyan-400">
          <Activity size={18} />
        </div>
      </div>

      <p className="mt-4 text-4xl font-bold text-white">{total}</p>
      <p className="text-sm text-slate-400">Total findings</p>

      <div className="mt-6 flex flex-1 flex-col justify-end gap-4">
        {rows.map((row) => {
          const count = counts[row.key];
          const width = count === 0 ? 0 : Math.max(4, (count / max) * 100);

          return (
            <div key={row.key}>
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium text-slate-300">{row.label}</span>
                <span className="font-mono text-slate-400">{count}</span>
              </div>
              <div className="mt-1.5 h-2 overflow-hidden rounded-full bg-slate-800">
                <div
                  className={cn("h-full rounded-full transition-all duration-700")}
                  style={{ width: `${width}%`, backgroundColor: severityColors[row.key] }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
