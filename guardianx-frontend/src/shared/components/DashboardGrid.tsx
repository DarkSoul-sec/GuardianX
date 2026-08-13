import type { ReactNode } from "react";

import { cn } from "@/shared/utils/cn";

interface Props {
  children: ReactNode;
  columns?: 2 | 3 | 4 | 5;
  className?: string;
}

/**
 * Responsive dashboard grid with a consistent gap.
 */
export default function DashboardGrid({
  children,
  columns = 3,
  className,
}: Props) {
  return (
    <div
      className={cn(
        "grid gap-6",
        {
          "md:grid-cols-2": columns === 2,
          "lg:grid-cols-3": columns === 3,
          "xl:grid-cols-4": columns === 4,
          "md:grid-cols-2 xl:grid-cols-5": columns === 5,
        },
        className
      )}
    >
      {children}
    </div>
  );
}
