import { Boxes, Loader, PauseCircle, Workflow } from "lucide-react";

import { DashboardGrid, Skeleton, StatCard } from "@/shared/components";

import type { ScanOperations } from "@/types/scan";

interface Props {
  data?: ScanOperations;
  loading?: boolean;
}

export default function ScanOperationsStatus({ data, loading = false }: Props) {
  if (loading || !data) {
    return (
      <DashboardGrid columns={5}>
        {Array.from({ length: 5 }).map((_, index) => (
          <Skeleton key={index} className="h-28 rounded-2xl" />
        ))}
      </DashboardGrid>
    );
  }

  const { executor, counts } = data;
  const running = counts.RUNNING ?? 0;
  const pending = counts.PENDING ?? 0;
  const queued = executor.queued + pending;

  return (
    <DashboardGrid columns={5}>
      <StatCard
        label="Active Scans"
        value={running}
        icon={<Loader size={20} />}
        accent="cyan"
      />
      <StatCard
        label="Queued"
        value={queued}
        icon={<PauseCircle size={20} />}
        accent="blue"
        hint={pending > 0 ? `${pending} waiting in scheduler` : undefined}
      />
      <StatCard
        label="Worker Pool"
        value={executor.max_workers}
        icon={<Workflow size={20} />}
        accent="blue"
        hint="Concurrent scan slots"
      />
      <StatCard
        label="Workers Active"
        value={executor.running}
        icon={<Loader size={20} />}
        accent="amber"
      />
      <StatCard
        label="Workers Idle"
        value={executor.idle_workers}
        icon={<Boxes size={20} />}
        accent="emerald"
        hint={executor.closed ? "Executor shutting down" : undefined}
      />
    </DashboardGrid>
  );
}
