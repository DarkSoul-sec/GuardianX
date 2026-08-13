import type { ReactNode } from "react";

import { cn } from "@/shared/utils/cn";
import { Skeleton } from "./Skeleton";

interface Props {
  title: string;
  subtitle?: string;
  action?: ReactNode;
  children: ReactNode;
  loading?: boolean;
  className?: string;
}

export default function ChartCard({
  title,
  subtitle,
  action,
  children,
  loading = false,
  className,
}: Props) {
  return (
    <div className={cn("panel p-6", className)}>
      <div className="mb-5 flex items-start justify-between">
        <div>
          <h2 className="font-display text-lg font-semibold tracking-wide text-slate-100">
            {title}
          </h2>
          {subtitle && <p className="mt-1 text-sm text-slate-400">{subtitle}</p>}
        </div>
        {action}
      </div>

      {loading ? (
        <Skeleton className="h-64 w-full" />
      ) : (
        <div className="flex justify-center">{children}</div>
      )}
    </div>
  );
}
