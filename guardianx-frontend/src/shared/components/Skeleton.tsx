import { cn } from "@/shared/utils/cn";

interface Props {
  className?: string;
}

export function Skeleton({ className }: Props) {
  return (
    <div
      aria-hidden
      className={cn(
        "animate-shimmer rounded-lg bg-gradient-to-r from-slate-800 via-slate-700 to-slate-800 bg-[length:200%_100%]",
        className
      )}
    />
  );
}

export function SkeletonCard({ className }: Props) {
  return (
    <div className={cn("panel p-6", className)}>
      <Skeleton className="mb-4 h-5 w-32" />
      <Skeleton className="h-10 w-20" />
    </div>
  );
}
