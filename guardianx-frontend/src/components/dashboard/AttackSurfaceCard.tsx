import type { ReactNode } from "react";
import { Radio, ScanSearch, ShieldAlert, Waypoints } from "lucide-react";

import Card from "@/shared/components/Card";

interface MetricProps {
  label: string;
  value: number;
  icon: ReactNode;
  accent: string;
  glow: string;
}

function Metric({ label, value, icon, accent, glow }: MetricProps) {
  return (
    <div className="group rounded-2xl border border-slate-800 bg-slate-950/50 p-4 transition hover:border-slate-700 hover:bg-slate-900/70">
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          {label}
        </p>
        <div
          className={`rounded-lg p-2 transition group-hover:shadow-[0_0_18px_var(--glow-color)] ${accent}`}
          style={{ "--glow-color": glow } as React.CSSProperties}
        >
          {icon}
        </div>
      </div>
      <p className="mt-3 font-mono text-3xl font-bold text-white">{value}</p>
    </div>
  );
}

interface Props {
  openPorts: number;
  totalServices: number;
  totalFindings: number;
  completedScans: number;
}

export default function AttackSurfaceCard({
  openPorts,
  totalServices,
  totalFindings,
  completedScans,
}: Props) {
  return (
    <Card className="space-y-5">
      <div>
        <h2 className="font-display text-xl font-bold tracking-wide text-slate-100">
          Attack Surface
        </h2>
        <p className="mt-0.5 text-sm text-slate-400">
          Exposure across your monitored estate.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Metric
          label="Open Ports"
          value={openPorts}
          icon={<Radio size={16} />}
          accent="text-red-400 bg-red-500/10"
          glow="rgba(255,59,92,0.35)"
        />
        <Metric
          label="Running Services"
          value={totalServices}
          icon={<Waypoints size={16} />}
          accent="text-cyan-400 bg-cyan-500/10"
          glow="rgba(0,207,255,0.35)"
        />
        <Metric
          label="Total Findings"
          value={totalFindings}
          icon={<ShieldAlert size={16} />}
          accent="text-amber-400 bg-amber-500/10"
          glow="rgba(255,210,59,0.35)"
        />
        <Metric
          label="Scans Completed"
          value={completedScans}
          icon={<ScanSearch size={16} />}
          accent="text-emerald-400 bg-emerald-500/10"
          glow="rgba(34,229,154,0.35)"
        />
      </div>
    </Card>
  );
}
