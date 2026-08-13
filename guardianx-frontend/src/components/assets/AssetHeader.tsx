import type { ReactNode } from "react";
import {
  Calendar,
  Clock,
  Globe,
  HardDrive,
  Network,
  Server,
  ShieldCheck,
  User,
} from "lucide-react";

import Badge from "@/shared/components/Badge";
import Card from "@/shared/components/Card";
import { formatDate } from "@/shared/utils/format";
import { cn } from "@/shared/utils/cn";

import type { AssetDetails, Criticality } from "@/types/asset";

interface FactProps {
  icon: ReactNode;
  label: string;
  value: string;
}

function Fact({ icon, label, value }: FactProps) {
  return (
    <div className="flex items-start gap-3">
      <div className="rounded-lg bg-slate-800 p-2 text-cyan-400">{icon}</div>
      <div className="min-w-0">
        <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
        <p className="mt-0.5 truncate font-mono text-sm text-slate-200">{value}</p>
      </div>
    </div>
  );
}

const criticalityColors: Record<Criticality, string> = {
  CRITICAL: "bg-red-600",
  HIGH: "bg-orange-500",
  MEDIUM: "bg-yellow-500",
  LOW: "bg-green-600",
};

function criticalityBadge(criticality: Criticality | null) {
  if (!criticality) return <Badge color="gray">UNKNOWN</Badge>;
  return (
    <Badge className={criticalityColors[criticality]}>
      {criticality.toUpperCase()}
    </Badge>
  );
}

interface Props {
  asset: AssetDetails;
}

export default function AssetHeader({ asset }: Props) {
  return (
    <Card className="p-6">
      <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="mr-2 text-3xl font-bold text-white">{asset.name}</h1>
            <Badge color="cyan">{asset.asset_type}</Badge>
            {asset.environment && (
              <Badge color="blue">{asset.environment.toUpperCase()}</Badge>
            )}
            {criticalityBadge(asset.criticality)}
          </div>

          <div className="mt-3 flex flex-wrap items-center gap-x-6 gap-y-1 text-sm text-slate-400">
            {asset.domain && (
              <span className="inline-flex items-center gap-1.5">
                <Globe size={14} /> {asset.domain}
              </span>
            )}
            {asset.ip_address && (
              <span className="inline-flex items-center gap-1.5">
                <Network size={14} /> {asset.ip_address}
              </span>
            )}
            {asset.operating_system && (
              <span className="inline-flex items-center gap-1.5">
                <HardDrive size={14} /> {asset.operating_system}
              </span>
            )}
          </div>

          {asset.description && (
            <p className="mt-4 max-w-2xl text-sm leading-relaxed text-slate-400">
              {asset.description}
            </p>
          )}
        </div>

        <div className="grid shrink-0 grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 lg:text-right">
          <Fact
            icon={<Server size={16} />}
            label="Hostname"
            value={asset.hostname ?? "-"}
          />
          <Fact
            icon={<Network size={16} />}
            label="IP Address"
            value={asset.ip_address ?? "-"}
          />
          <Fact
            icon={<Globe size={16} />}
            label="Domain"
            value={asset.domain ?? "-"}
          />
          <Fact
            icon={<User size={16} />}
            label="Owner"
            value={asset.owner ?? "-"}
          />
          <Fact
            icon={<Calendar size={16} />}
            label="Created"
            value={formatDate(asset.created_at)}
          />
          <Fact
            icon={<Clock size={16} />}
            label="Last Updated"
            value={formatDate(asset.updated_at)}
          />
        </div>
      </div>

      {asset.ai_summary && (
        <div
          className={cn(
            "mt-6 flex items-start gap-3 rounded-xl border border-slate-800",
            "bg-slate-950/60 p-4"
          )}
        >
          <ShieldCheck size={18} className="mt-0.5 shrink-0 text-cyan-400" />
          <p className="text-sm leading-relaxed text-slate-300">
            {asset.ai_summary}
          </p>
        </div>
      )}
    </Card>
  );
}
