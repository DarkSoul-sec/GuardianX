import { ScanLine } from "lucide-react";

import StatusBadge from "@/shared/components/StatusBadge";

import TimelineCard from "@/shared/components/TimelineCard";
import { formatRelativeTime } from "@/shared/utils/format";

import type { RecentScan } from "@/types/dashboard";

interface Props {
  scans: RecentScan[];
}

export default function RecentScansCard({ scans }: Props) {
  return (
    <TimelineCard
      title="Recent Scans"
      items={scans.map((scan) => ({
        id: scan.scan_id,
        title: scan.asset_name,
        subtitle: [
          `${scan.finding_count} finding${scan.finding_count === 1 ? "" : "s"}`,
          formatRelativeTime(scan.started_at),
        ].join(" • "),
        icon: <ScanLine size={16} />,
        badge: <StatusBadge status={scan.status} />,
      }))}
      emptyMessage="No scans have run yet."
    />
  );
}
