import { CheckCircle, CircleAlert, ListChecks, ShieldAlert, UserCheck } from "lucide-react";

import { useFindingsStats } from "@/hooks/useFindings";
import { DashboardGrid, Skeleton, StatCard } from "@/shared/components";

interface Props {
  loading?: boolean;
}

export default function FindingStats({ loading = false }: Props) {
  const { data, isLoading } = useFindingsStats();
  const busy = loading || isLoading;

  if (busy || !data) {
    return (
      <DashboardGrid columns={5}>
        {Array.from({ length: 5 }).map((_, index) => (
          <Skeleton key={index} className="h-28 rounded-2xl" />
        ))}
      </DashboardGrid>
    );
  }

  const highPriority =
    (data.by_severity.CRITICAL ?? 0) + (data.by_severity.HIGH ?? 0);

  return (
    <DashboardGrid columns={5}>
      <StatCard
        label="Open"
        value={data.open}
        icon={<CircleAlert size={20} />}
        accent="rose"
        hint={`${highPriority} critical/high need review`}
      />
      <StatCard
        label="In Progress"
        value={data.in_progress}
        icon={<UserCheck size={20} />}
        accent="amber"
      />
      <StatCard
        label="Resolved"
        value={data.resolved}
        icon={<CheckCircle size={20} />}
        accent="emerald"
      />
      <StatCard
        label="False Positive"
        value={data.false_positive}
        icon={<ShieldAlert size={20} />}
        accent="blue"
      />
      <StatCard
        label="Accepted Risk"
        value={data.accepted_risk}
        icon={<ListChecks size={20} />}
        accent="cyan"
        suffix={`/ ${data.total}`}
      />
    </DashboardGrid>
  );
}
