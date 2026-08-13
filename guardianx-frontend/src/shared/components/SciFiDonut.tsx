import { useId } from "react";
import { motion } from "framer-motion";
import {
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  type TooltipContentProps,
} from "recharts";

import { cn } from "@/shared/utils/cn";

export interface DonutSegment {
  name: string;
  value: number;
  from: string;
  to: string;
  text?: string;
  dot?: string;
}

interface Props {
  data: DonutSegment[];
  centerValue?: number | string;
  centerLabel?: string;
  className?: string;
  height?: number;
  legend?: boolean;
}

/**
 * Futuristic segmented donut: gradient slices with a neon glow, animated
 * center readout and a custom glass tooltip.
 */
export default function SciFiDonut({
  data,
  centerValue,
  centerLabel,
  className,
  height = 224,
  legend = false,
}: Props) {
  const id = useId();
  const uid = id.replace(/:/g, "");

  const segments = data.filter((entry) => entry.value > 0);
  const total = segments.reduce((sum, entry) => sum + entry.value, 0);

  function renderTooltip({ active, payload }: TooltipContentProps) {
    if (!active || !payload?.length) return null;
    const entry = payload[0].payload as
      | { name: string; value: number }
      | undefined;
    if (!entry) return null;
    const percent = total > 0 ? Math.round((entry.value / total) * 100) : 0;

    return (
      <div className="rounded-xl border border-slate-700 bg-slate-950/95 px-3.5 py-2.5 shadow-xl shadow-black/40 backdrop-blur">
        <p className="text-xs font-semibold text-slate-200">{entry.name}</p>
        <p className="mt-0.5 font-mono text-sm font-bold text-white">
          {entry.value}{" "}
          <span className="text-xs font-normal text-slate-400">
            · {percent}%
          </span>
        </p>
      </div>
    );
  }

  return (
    <div className={cn("w-full", className)}>
      <div className="relative" style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <defs>
              {segments.map((segment, index) => (
                <linearGradient
                  key={`grad-${index}`}
                  id={`${uid}-grad-${index}`}
                  x1="0%"
                  y1="0%"
                  x2="100%"
                  y2="100%"
                >
                  <stop offset="0%" stopColor={segment.from} />
                  <stop offset="100%" stopColor={segment.to} />
                </linearGradient>
              ))}
              {segments.map((segment, index) => (
                <filter
                  key={`glow-${index}`}
                  id={`${uid}-glow-${index}`}
                  x="-30%"
                  y="-30%"
                  width="160%"
                  height="160%"
                >
                  <feDropShadow
                    dx="0"
                    dy="0"
                    stdDeviation="3.5"
                    floodColor={segment.from}
                    floodOpacity="0.6"
                  />
                </filter>
              ))}
            </defs>
            <Pie
              data={segments}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              innerRadius="62%"
              outerRadius="92%"
              paddingAngle={3}
              cornerRadius={7}
              stroke="#0b1220"
              strokeWidth={2}
              animationBegin={120}
              animationDuration={900}
              animationEasing="ease-out"
            >
              {segments.map((segment, index) => (
                <Cell
                  key={segment.name}
                  fill={`url(#${uid}-grad-${index})`}
                  filter={`url(#${uid}-glow-${index})`}
                />
              ))}
            </Pie>
            <Tooltip content={renderTooltip} />
          </PieChart>
        </ResponsiveContainer>

        {(centerValue !== undefined || centerLabel) && (
          <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
            {centerValue !== undefined && (
              <motion.span
                initial={{ opacity: 0, scale: 0.7 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.6, delay: 0.35 }}
                className="font-mono text-3xl font-bold tabular-nums text-white"
              >
                {centerValue}
              </motion.span>
            )}
            {centerLabel && (
              <span className="mt-1 text-[10px] font-semibold uppercase tracking-[0.25em] text-slate-500">
                {centerLabel}
              </span>
            )}
          </div>
        )}
      </div>

      {legend && (
        <div className="mt-4 grid grid-cols-2 gap-2">
          {segments.map((segment) => {
            const percent =
              total > 0 ? Math.round((segment.value / total) * 100) : 0;
            return (
              <div
                key={segment.name}
                className="rounded-lg border border-slate-800 bg-slate-950/60 px-3 py-2.5"
              >
                <div className="flex items-center gap-1.5">
                  <i
                    className={cn(
                      "h-2 w-2 rounded-full",
                      segment.dot ?? "shadow-[0_0_6px_currentColor]"
                    )}
                    style={
                      segment.dot
                        ? undefined
                        : { backgroundColor: segment.from, color: segment.from }
                    }
                  />
                  <span className="text-xs text-slate-400">{segment.name}</span>
                </div>
                <div className="mt-1 flex items-baseline justify-between">
                  <span
                    className={cn(
                      "font-mono text-lg font-bold",
                      segment.text ?? "text-white"
                    )}
                  >
                    {segment.value}
                  </span>
                  <span className="font-mono text-[10px] text-slate-500">
                    {percent}%
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
