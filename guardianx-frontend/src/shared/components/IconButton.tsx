import type { ButtonHTMLAttributes, ReactNode } from "react";

import { cn } from "@/shared/utils/cn";

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  label: string;
  colorClass?: string;
  children: ReactNode;
}

export default function IconButton({
  label,
  colorClass = "bg-slate-800 hover:bg-slate-700",
  className,
  children,
  ...props
}: Props) {
  return (
    <button
      {...props}
      aria-label={label}
      title={label}
      className={cn(
        "rounded-lg p-3 text-white transition disabled:cursor-not-allowed disabled:opacity-40",
        colorClass,
        className
      )}
    >
      {children}
    </button>
  );
}
