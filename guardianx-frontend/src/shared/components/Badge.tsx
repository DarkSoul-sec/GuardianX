import type { ReactNode } from "react";

import { cn } from "@/shared/utils/cn";

type PaletteColor =
  | "red"
  | "orange"
  | "yellow"
  | "green"
  | "cyan"
  | "blue"
  | "gray"
  | "amber";

interface Props {
  children: ReactNode;
  color?: PaletteColor;
  tone?: "severity" | "status" | "neutral";
  className?: string;
}

/**
 * Tailwind class maps, keyed by semantic name. Kept local to the design
 * system so application code never embeds color literals.
 */
const classes: Record<PaletteColor, string> = {
  red: "border-red-500/40 bg-red-500/15 text-red-300",
  orange: "border-orange-500/40 bg-orange-500/15 text-orange-300",
  yellow: "border-yellow-500/40 bg-yellow-500/15 text-yellow-300",
  green: "border-green-500/40 bg-green-500/15 text-green-300",
  cyan: "border-cyan-400/40 bg-cyan-500/15 text-cyan-300",
  blue: "border-blue-500/40 bg-blue-500/15 text-blue-300",
  amber: "border-amber-500/40 bg-amber-500/15 text-amber-300",
  gray: "border-slate-500/40 bg-slate-500/15 text-slate-300",
};

const toneDefaults: Record<NonNullable<Props["tone"]>, PaletteColor> = {
  severity: "gray",
  status: "gray",
  neutral: "gray",
};

export default function Badge({
  children,
  color,
  tone = "neutral",
  className,
}: Props) {
  const palette = color ?? toneDefaults[tone];

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-3 py-0.5 font-mono text-xs font-semibold uppercase tracking-wide",
        classes[palette],
        className
      )}
    >
      <i
        aria-hidden="true"
        className="h-1.5 w-1.5 shrink-0 rounded-full bg-current shadow-[0_0_8px_currentColor]"
      />
      {children}
    </span>
  );
}
