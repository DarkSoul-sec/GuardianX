import type { SelectHTMLAttributes } from "react";

import { cn } from "@/shared/utils/cn";

interface Props extends SelectHTMLAttributes<HTMLSelectElement> {
  className?: string;
}

export default function Select({ className = "", ...props }: Props) {
  return (
    <select
      {...props}
      className={cn(
        "field cursor-pointer [&>option]:bg-slate-900",
        className
      )}
    />
  );
}
