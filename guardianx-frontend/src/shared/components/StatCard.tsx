import type { ReactNode } from "react";

import { cn } from "@/shared/utils/cn";

interface Props {
  label: string;
  value: number | string;
  icon?: ReactNode;
  accent?: "cyan" | "emerald" | "amber" | "rose" | "blue";
  suffix?: string;
  hint?: string;
  animate?: boolean;
  className?: string;
}

const accents = {
  cyan: "text-cyan-300 bg-cyan-500/10 border-cyan-400/30 shadow-[0_0_18px_rgba(0,207,255,0.25)]",
  emerald: "text-emerald-300 bg-emerald-500/10 border-emerald-400/30 shadow-[0_0_18px_rgba(34,229,154,0.25)]",
  amber: "text-amber-300 bg-amber-500/10 border-amber-400/30 shadow-[0_0_18px_rgba(255,210,59,0.25)]",
  rose: "text-rose-300 bg-rose-500/10 border-rose-400/30 shadow-[0_0_18px_rgba(255,59,92,0.25)]",
  blue: "text-blue-300 bg-blue-500/10 border-blue-400/30 shadow-[0_0_18px_rgba(59,130,246,0.25)]",
} as const;

export default function StatCard({
  label,
  value,
  icon,
  accent = "cyan",
  suffix = "",
  hint,
  animate = true,
  className,
}: Props) {
  const accentClass = accents[accent];
  const displayValue =
    typeof value === "number" && animate
      ? value.toLocaleString()
      : String(value);

  return (
    <div className={cn("panel panel-hover p-6", className)}>
      <div className="flex items-center justify-between">
        <p className="eyebrow">{label}</p>
        {icon && (
          <div
            className={cn(
              "rounded-xl border p-3",
              accentClass
            )}
          >
            {icon}
          </div>
        )}
      </div>

      <div className="mt-3 font-mono text-3xl font-bold text-white">
        <span className="glow-text">{displayValue}</span>
        {suffix && <span className="ml-1 text-lg text-slate-400">{suffix}</span>}
      </div>

      {hint && <p className="mt-2 text-xs text-slate-500">{hint}</p>}
    </div>
  );
}
