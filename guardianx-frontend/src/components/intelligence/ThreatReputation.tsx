import { motion } from "framer-motion";
import {
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  type TooltipContentProps,
} from "recharts";
import { Crosshair, ShieldAlert, Tag, Vote } from "lucide-react";

import { Badge, Card, DashboardGrid } from "@/shared/components";

import type { IntelligenceReport } from "@/types/intelligence";

interface Props {
  report: IntelligenceReport;
}

type VerdictKey = "malicious" | "suspicious" | "harmless" | "undetected";

const SEGMENTS: {
  key: VerdictKey;
  label: string;
  from: string;
  to: string;
  text: string;
  dot: string;
}[] = [
  {
    key: "malicious",
    label: "Malicious",
    from: "#fb7185",
    to: "#881337",
    text: "text-rose-300",
    dot: "bg-rose-500",
  },
  {
    key: "suspicious",
    label: "Suspicious",
    from: "#fbbf24",
    to: "#78350f",
    text: "text-amber-300",
    dot: "bg-amber-500",
  },
  {
    key: "harmless",
    label: "Harmless",
    from: "#34d399",
    to: "#064e3b",
    text: "text-emerald-300",
    dot: "bg-emerald-500",
  },
  {
    key: "undetected",
    label: "Undetected",
    from: "#94a3b8",
    to: "#1e293b",
    text: "text-slate-300",
    dot: "bg-slate-600",
  },
];

function VerdictDonut({ report }: { report: IntelligenceReport }) {
  const data = SEGMENTS.map((segment) => ({
    ...segment,
    value: report[segment.key],
  })).filter((entry) => entry.value > 0);

  const total = Math.max(0, report.total);

  function renderTooltip({ active, payload }: TooltipContentProps) {
    if (!active || !payload?.length) return null;
    const entry = payload[0].payload as
      | { label: string; value: number }
      | undefined;
    if (!entry) return null;
    const percent = total > 0 ? Math.round((entry.value / total) * 100) : 0;

    return (
      <div className="rounded-xl border border-slate-700 bg-slate-950/95 px-3.5 py-2.5 shadow-xl shadow-black/40 backdrop-blur">
        <p className="text-xs font-semibold text-slate-200">{entry.label}</p>
        <p className="mt-0.5 font-mono text-sm font-bold text-white">
          {entry.value}{" "}
          <span className="text-xs font-normal text-slate-400">
            engines · {percent}%
          </span>
        </p>
      </div>
    );
  }

  return (
    <div>
      {data.length === 0 ? (
        <p className="py-16 text-center text-sm text-slate-500">
          No vendor verdicts reported.
        </p>
      ) : (
        <>
          <div className="relative h-56">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <defs>
                  {SEGMENTS.map((segment) => (
                    <linearGradient
                      key={`grad-${segment.key}`}
                      id={`vg-${segment.key}`}
                      x1="0%"
                      y1="0%"
                      x2="100%"
                      y2="100%"
                    >
                      <stop offset="0%" stopColor={segment.from} />
                      <stop offset="100%" stopColor={segment.to} />
                    </linearGradient>
                  ))}
                  {SEGMENTS.map((segment) => (
                    <filter
                      key={`glow-${segment.key}`}
                      id={`vg-glow-${segment.key}`}
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
                  data={data}
                  dataKey="value"
                  nameKey="label"
                  cx="50%"
                  cy="50%"
                  innerRadius={62}
                  outerRadius={94}
                  paddingAngle={3}
                  cornerRadius={7}
                  stroke="#0b1220"
                  strokeWidth={2}
                  animationBegin={120}
                  animationDuration={900}
                  animationEasing="ease-out"
                >
                  {data.map((entry) => (
                    <Cell
                      key={entry.key}
                      fill={`url(#vg-${entry.key})`}
                      filter={`url(#vg-glow-${entry.key})`}
                    />
                  ))}
                </Pie>
                <Tooltip content={renderTooltip} />
              </PieChart>
            </ResponsiveContainer>

            <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
              <motion.span
                initial={{ opacity: 0, scale: 0.7 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.6, delay: 0.35 }}
                className="font-mono text-4xl font-bold tabular-nums text-white"
              >
                {total}
              </motion.span>
              <span className="mt-1 text-[10px] font-semibold uppercase tracking-[0.25em] text-slate-500">
                Engines
              </span>
            </div>
          </div>

          <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
            {SEGMENTS.map((segment) => {
              const count = report[segment.key];
              const percent = total > 0 ? Math.round((count / total) * 100) : 0;
              return (
                <div
                  key={segment.key}
                  className="rounded-lg border border-slate-800 bg-slate-950/60 px-3 py-2.5"
                >
                  <div className="flex items-center gap-1.5">
                    <i className={`h-2 w-2 rounded-full ${segment.dot}`} />
                    <span className="text-xs text-slate-400">{segment.label}</span>
                  </div>
                  <div className="mt-1 flex items-baseline justify-between">
                    <span className={`font-mono text-lg font-bold ${segment.text}`}>
                      {count}
                    </span>
                    <span className="font-mono text-[10px] text-slate-500">
                      {percent}%
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}

function ChipList({
  title,
  icon,
  items,
  emptyText,
}: {
  title: string;
  icon: React.ReactNode;
  items: string[];
  emptyText: string;
}) {
  return (
    <div>
      <p className="eyebrow mb-3 flex items-center gap-2">
        {icon}
        {title}
      </p>
      {items.length > 0 ? (
        <div className="flex flex-wrap gap-2">
          {items.map((item) => (
            <Badge key={item} color="gray">
              {item}
            </Badge>
          ))}
        </div>
      ) : (
        <p className="text-sm text-slate-500">{emptyText}</p>
      )}
    </div>
  );
}

export default function ThreatReputation({ report }: Props) {
  return (
    <Card className="space-y-6">
      <div>
        <p className="eyebrow mb-3 flex items-center gap-2">
          <ShieldAlert size={14} />
          Vendor Verdict Distribution
        </p>
        <VerdictDonut report={report} />
      </div>

      <DashboardGrid columns={2} className="gap-4">
        <div>
          <p className="eyebrow mb-3 flex items-center gap-2">
            <Vote size={14} />
            Community Votes
          </p>
          <div className="space-y-2 text-sm">
            <div className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-950/60 px-4 py-2.5">
              <span className="text-slate-400">Malicious</span>
              <span className="font-mono font-bold text-rose-300">
                {report.community_votes.malicious}
              </span>
            </div>
            <div className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-950/60 px-4 py-2.5">
              <span className="text-slate-400">Harmless</span>
              <span className="font-mono font-bold text-emerald-300">
                {report.community_votes.harmless}
              </span>
            </div>
          </div>
        </div>

        <div>
          <ChipList
            title="Categories"
            icon={<Tag size={14} />}
            items={report.categories}
            emptyText="No vendor categories reported."
          />
        </div>
      </DashboardGrid>

      <ChipList
        title="Tags"
        icon={<Tag size={14} />}
        items={report.tags}
        emptyText="No tags reported."
      />

      <div>
        <p className="eyebrow mb-3 flex items-center gap-2">
          <Crosshair size={14} />
          MITRE ATT&amp;CK Mapping
        </p>
        {report.mitre.length > 0 ? (
          <div className="grid gap-3 md:grid-cols-2">
            {report.mitre.map((mapping) => (
              <div
                key={mapping.technique_id}
                className="rounded-xl border border-slate-800 bg-slate-950/60 p-4"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono text-xs font-semibold uppercase tracking-wider text-violet-300">
                    {mapping.technique_id}
                  </span>
                  <Badge color="blue">{mapping.tactic}</Badge>
                </div>
                <p className="mt-2 font-semibold text-white">{mapping.technique}</p>
                {mapping.description && (
                  <p className="mt-1 text-xs text-slate-400">{mapping.description}</p>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-slate-500">
            No MITRE ATT&amp;CK techniques could be inferred from the reported tags.
          </p>
        )}
      </div>
    </Card>
  );
}
