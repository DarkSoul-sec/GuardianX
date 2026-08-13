import { Globe, Layers, Radio, Waypoints } from "lucide-react";

import Badge from "@/shared/components/Badge";
import Card from "@/shared/components/Card";
import DataTable from "@/shared/components/DataTable";
import type { Column } from "@/shared/components/DataTable";

import type { AssetDetails, AssetServiceItem } from "@/types/asset";

const serviceColumns: Column<AssetServiceItem>[] = [
  { key: "port", title: "Port" },
  { key: "protocol", title: "Protocol" },
  { key: "product", title: "Product" },
  { key: "version", title: "Version" },
  {
    key: "cpe",
    title: "CPE",
    render: (row) =>
      row.cpe ? (
        <span className="font-mono text-xs text-slate-400">{row.cpe}</span>
      ) : (
        <span className="text-slate-600">-</span>
      ),
  },
  {
    key: "state",
    title: "State",
    render: (row) => <Badge color="green">{row.state}</Badge>,
  },
];

interface ChipProps {
  children: string | number;
}

function Chip({ children }: ChipProps) {
  return (
    <span className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-1 font-mono text-xs text-slate-200">
      {children}
    </span>
  );
}

interface Props {
  asset: AssetDetails;
}

export default function AttackSurface({ asset }: Props) {
  const exposedCount = asset.services.filter(
    (service) => service.state === "open"
  ).length;

  return (
    <Card className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="rounded-xl bg-cyan-500/10 p-2 text-cyan-400">
            <Globe size={18} />
          </div>
          <h2 className="text-xl font-bold">Attack Surface</h2>
        </div>
        <Badge color={asset.internet_facing ? "red" : "green"}>
          {asset.internet_facing ? "INTERNET FACING" : "INTERNAL"}
        </Badge>
      </div>

      <div className="grid gap-6 sm:grid-cols-2">
        <div>
          <div className="mb-3 flex items-center gap-2 text-sm text-slate-400">
            <Radio size={14} />
            <span className="font-semibold uppercase tracking-wide">
              Open Ports ({asset.open_ports.length})
            </span>
          </div>
          {asset.open_ports.length === 0 ? (
            <p className="text-sm text-slate-500">No open ports detected.</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {asset.open_ports.map((port) => (
                <Chip key={port}>{port}</Chip>
              ))}
            </div>
          )}
        </div>

        <div>
          <div className="mb-3 flex items-center gap-2 text-sm text-slate-400">
            <Layers size={14} />
            <span className="font-semibold uppercase tracking-wide">
              Technology Stack ({asset.technologies.length})
            </span>
          </div>
          {asset.technologies.length === 0 ? (
            <p className="text-sm text-slate-500">
              No technologies fingerprinted yet.
            </p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {asset.technologies.map((technology) => (
                <Chip key={technology}>{technology}</Chip>
              ))}
            </div>
          )}
        </div>
      </div>

      <div>
        <div className="mb-3 flex items-center gap-2 text-sm text-slate-400">
          <Waypoints size={14} />
          <span className="font-semibold uppercase tracking-wide">
            Running Services ({exposedCount})
          </span>
        </div>
        <DataTable
          columns={serviceColumns}
          data={asset.services}
          rowKey={(row) => `${row.port}-${row.protocol}`}
          emptyText="No services discovered for this asset."
        />
      </div>
    </Card>
  );
}
