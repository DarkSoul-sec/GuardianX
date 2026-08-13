import { Activity, CheckCircle2, Clock, XCircle } from "lucide-react";

import { DashboardGrid, StatCard } from "@/shared/components";

import type { Scan } from "@/types/scan";

interface Props {
  scans: Scan[];
  loading: boolean;
}

export default function ScanStats({ scans, loading }: Props) {
  const running = scans.filter((scan) => scan.status === "RUNNING").length;
  const pending = scans.filter((scan) => scan.status === "PENDING").length;
  const completed = scans.filter((scan) => scan.status === "COMPLETED").length;
  const failed = scans.filter((scan) => scan.status === "FAILED").length;
  const successRate =
    completed + failed === 0
      ? null
      : Math.round((completed / (completed + failed)) * 100);

  return (
    <DashboardGrid columns={4}>
      <StatCard
        label="Running"
        value={running}
        icon={<Clock size={20} />}
        accent="cyan"
        hint={pending > 0 ? `${pending} queued` : undefined}
      />
      <StatCard
        label="Completed"
        value={completed}
        icon={<CheckCircle2 size={20} />}
        accent="emerald"
      />
      <StatCard
        label="Failed"
        value={failed}
        icon={<XCircle size={20} />}
        accent="rose"
      />
      <StatCard
        label="Success Rate"
        value={successRate ?? "-"}
        suffix={successRate === null ? "" : "%"}
        icon={<Activity size={20} />}
        accent="amber"
        hint={loading ? "Loading..." : "Completed vs failed"}
      />
    </DashboardGrid>
  );
}
