import type { ReactNode } from "react";

interface Props {
  title: string;
  subtitle?: string;
  action?: ReactNode;
}

export default function PageHeader({
  title,
  subtitle,
  action,
}: Props) {
  return (
    <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
      <div>
        <p className="eyebrow mb-1 flex items-center gap-2">
          <span className="inline-block h-px w-8 bg-gradient-to-r from-cyan-400 to-transparent" />
          GuardianX Console
        </p>
        <h1 className="font-display text-3xl font-bold tracking-wide text-slate-50 md:text-4xl">
          <span className="neon-text">{title}</span>
        </h1>
        {subtitle && <p className="mt-2 text-slate-400">{subtitle}</p>}
      </div>
      {action && <div className="flex items-center gap-2">{action}</div>}
    </div>
  );
}
