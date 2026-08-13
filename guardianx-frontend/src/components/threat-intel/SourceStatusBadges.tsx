import { CloudOff, Cloudy, Database, Radar, ShieldAlert, Timer } from "lucide-react";

import { Badge, Skeleton } from "@/shared/components";
import type { SourceStatus } from "@/types/threat-intel";

const SOURCE_META: Record<
  string,
  { label: string; icon: typeof Radar }
> = {
  nvd: { label: "NVD", icon: Database },
  cisa_kev: { label: "CISA KEV", icon: ShieldAlert },
  epss: { label: "EPSS", icon: Timer },
  mitre_attck: { label: "MITRE ATT&CK", icon: Radar },
};

interface Props {
  sources?: SourceStatus[];
  loading?: boolean;
}

export default function SourceStatusBadges({ sources, loading }: Props) {
  if (loading) {
    return (
      <div className="flex flex-wrap gap-2">
        <Skeleton className="h-7 w-20 rounded-full" />
        <Skeleton className="h-7 w-24 rounded-full" />
        <Skeleton className="h-7 w-16 rounded-full" />
        <Skeleton className="h-7 w-28 rounded-full" />
      </div>
    );
  }

  return (
    <div className="flex flex-wrap gap-2">
      {(sources ?? []).map((source) => {
        const meta = SOURCE_META[source.source];
        const Icon = meta?.icon ?? Cloudy;

        if (!source.healthy) {
          return (
            <Badge key={source.source} color="red">
              <CloudOff size={12} />
              {meta?.label ?? source.source} offline
            </Badge>
          );
        }

        return (
          <Badge key={source.source} color="green">
            <Icon size={12} />
            {meta?.label ?? source.source} live
          </Badge>
        );
      })}
    </div>
  );
}
