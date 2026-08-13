import { Activity, Shield } from "lucide-react";

export default function DashboardHeader() {
  return (
    <div className="relative mb-8 overflow-hidden rounded-3xl border border-slate-800/80 bg-gradient-to-br from-slate-900/80 via-slate-900/60 to-cyan-950/40 p-6 shadow-[0_24px_60px_-24px_rgba(0,0,0,0.85)] backdrop-blur-xl md:p-8">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -right-24 -top-24 h-64 w-64 rounded-full bg-cyan-500/10 blur-3xl"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -bottom-28 -left-16 h-64 w-64 rounded-full bg-violet-500/10 blur-3xl"
      />

      <div className="relative flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow mb-1.5 flex items-center gap-2">
            <span className="inline-block h-px w-8 bg-gradient-to-r from-cyan-400 to-transparent" />
            Attack Surface Management
          </p>
          <h1 className="font-display text-3xl font-bold tracking-wide text-slate-50 md:text-4xl">
            <span className="neon-text glow-text">Security Center</span>
          </h1>
          <p className="mt-2 flex items-center gap-2 text-slate-400">
            <Activity size={14} className="text-cyan-400" />
            AI Powered Attack Surface Management
          </p>
        </div>

        <div className="flex items-center gap-3 rounded-2xl border border-cyan-400/30 bg-cyan-500/10 px-5 py-3 shadow-glow-soft backdrop-blur-sm">
          <span className="relative flex h-2.5 w-2.5">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60" />
            <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-emerald-400" />
          </span>
          <Shield className="text-cyan-300" size={26} />
          <div>
            <p className="eyebrow">Platform</p>
            <p className="font-display text-sm font-semibold tracking-wider text-cyan-200">
              GuardianX v2.6
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
