import type { ReactNode } from "react";

import { cn } from "@/shared/utils/cn";

interface Props {
  title: string;
  description?: string;
  icon?: ReactNode;
  action?: ReactNode;
  className?: string;
}

export default function EmptyState({
  title,
  description,
  icon,
  action,
  className,
}: Props) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-700/60 bg-slate-900/40 px-8 py-16 text-center",
        className
      )}
    >
      {icon && (
        <div className="mb-4 rounded-2xl border border-cyan-400/30 bg-cyan-500/10 p-4 text-cyan-300 shadow-glow-soft">
          {icon}
        </div>
      )}

      <h3 className="font-display text-xl font-semibold tracking-wide text-white">
        {title}
      </h3>

      {description && (
        <p className="mt-2 max-w-md text-sm text-slate-400">{description}</p>
      )}

      {action && <div className="mt-6">{action}</div>}
    </div>
  );
}
