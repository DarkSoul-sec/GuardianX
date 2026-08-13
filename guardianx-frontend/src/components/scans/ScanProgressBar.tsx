import { motion } from "framer-motion";

import { cn } from "@/shared/utils/cn";

import type { ScanStatus } from "@/types/scan";

interface Props {
  progress: number;
  status: ScanStatus;
  className?: string;
}

const statusBarColor: Record<ScanStatus, string> = {
  PENDING: "bg-amber-500",
  RUNNING: "bg-cyan-500",
  COMPLETED: "bg-emerald-500",
  FAILED: "bg-red-500",
  CANCELLED: "bg-slate-500",
};

const statusTextColor: Record<ScanStatus, string> = {
  PENDING: "text-amber-400",
  RUNNING: "text-cyan-400",
  COMPLETED: "text-emerald-400",
  FAILED: "text-red-400",
  CANCELLED: "text-slate-400",
};

export default function ScanProgressBar({ progress, status, className }: Props) {
  const running = status === "RUNNING";
  const clamped = Math.max(0, Math.min(100, progress));

  return (
    <div className={cn("w-full", className)}>
      <div className="flex items-center justify-between text-xs">
        <span className={cn("font-semibold", statusTextColor[status])}>
          {status === "RUNNING" ? `${clamped}% estimated` : `${clamped}%`}
        </span>
        <span className="text-slate-500">
          {status === "PENDING" ? "Queued" : status === "RUNNING" ? "In progress" : status === "COMPLETED" ? "Done" : "Stopped"}
        </span>
      </div>

      <div className="relative mt-1.5 h-2 overflow-hidden rounded-full bg-slate-800">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${clamped}%` }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className={cn("relative h-full rounded-full", statusBarColor[status])}
        >
          {running && (
            <motion.span
              aria-hidden
              className="absolute inset-y-0 w-1/3 bg-white/30"
              animate={{ x: ["-100%", "300%"] }}
              transition={{
                repeat: Infinity,
                duration: 1.2,
                ease: "linear",
              }}
            />
          )}
        </motion.div>
      </div>
    </div>
  );
}
