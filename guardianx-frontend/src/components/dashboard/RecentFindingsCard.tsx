import { Bug } from "lucide-react";

import SeverityBadge from "@/shared/components/SeverityBadge";
import StatusBadge from "@/shared/components/StatusBadge";

import TimelineCard from "@/shared/components/TimelineCard";
import { formatRelativeTime, truncate } from "@/shared/utils/format";

import type { RecentFinding } from "@/types/dashboard";

interface Props {
  findings: RecentFinding[];
}

export default function RecentFindingsCard({ findings }: Props) {
  return (
    <TimelineCard
      title="Recent Findings"
      items={findings.map((finding, index) => ({
        id: `${finding.title}-${index}`,
        title: finding.cve ? `${finding.cve} — ${truncate(finding.title, 34)}` : truncate(finding.title, 40),
        subtitle: `${finding.asset} • ${formatRelativeTime(finding.created_at)}`,
        timestamp: undefined,
        icon: <Bug size={16} />,
        badge: (
          <span className="flex gap-1.5">
            <SeverityBadge severity={finding.severity} />
            <StatusBadge status={finding.status} />
          </span>
        ),
      }))}
      emptyMessage="No findings detected."
    />
  );
}
