import { ScanLine } from "lucide-react";

import StatusBadge from "@/shared/components/StatusBadge";

import TimelineCard from "@/shared/components/TimelineCard";
import { formatDuration, formatRelativeTime } from "@/shared/utils/format";

import type { AssetDetails } from "@/types/asset";

interface Props {
  asset: AssetDetails;
}

export default function RecentScansTimeline({ asset }: Props) {
  return (
    <TimelineCard
      title="Recent Scans"
      items={asset.recent_scans.map((scan) => ({
        id: scan.scan_id,
        title: `Scan #${scan.scan_id}`,
        icon: <ScanLine size={16} />,
        timestamp: formatRelativeTime(scan.started_at),
        badge: <StatusBadge status={scan.status} />,
        subtitle: [
          `${scan.total_findings} finding${scan.total_findings === 1 ? "" : "s"}`,
          `duration ${formatDuration(scan.started_at, scan.finished_at)}`,
        ].join(" • "),
      }))}
      emptyMessage="No scans have been run for this asset."
    />
  );
}
