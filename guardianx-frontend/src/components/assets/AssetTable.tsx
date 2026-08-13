import { motion } from "framer-motion";
import {
  Pencil,
  Trash2,
  Server,
  Globe,
  Smartphone,
  Cloud,
  Monitor,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import type { ReactNode } from "react";

import { Card, EmptyState, IconButton, Skeleton } from "@/shared/components";

import ScanOptionsMenu from "@/components/assets/ScanOptionsMenu";

import type { Asset, Criticality } from "@/types/asset";
import type { ScanProfile } from "@/types/scan";

interface Props {
  assets: Asset[];
  loading: boolean;
  scanningId: number | null;
  onEdit: (asset: Asset) => void;
  onDelete: (asset: Asset) => void;
  onScan: (asset: Asset, profile: ScanProfile) => void;
}

function icon(type: string): ReactNode {
  switch (type) {
    case "SERVER":
      return <Server size={22} />;
    case "WEBSITE":
      return <Globe size={22} />;
    case "CLOUD":
      return <Cloud size={22} />;
    case "MOBILE":
      return <Smartphone size={22} />;
    default:
      return <Monitor size={22} />;
  }
}

const badges: Record<Criticality | "UNKNOWN", string> = {
  CRITICAL: "bg-red-500/20 text-red-400",
  HIGH: "bg-orange-500/20 text-orange-300",
  MEDIUM: "bg-yellow-500/20 text-yellow-300",
  LOW: "bg-green-500/20 text-green-300",
  UNKNOWN: "bg-slate-500/20 text-slate-300",
};

export default function AssetTable({
  assets,
  loading,
  scanningId,
  onEdit,
  onDelete,
  onScan,
}: Props) {
  const navigate = useNavigate();

  if (loading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <Skeleton key={index} className="h-28 w-full" />
        ))}
      </div>
    );
  }

  if (!assets.length) {
    return (
      <EmptyState
        title="No Assets Found"
        description="Create your first asset to begin vulnerability scanning."
        icon={<Server size={55} />}
      />
    );
  }

  return (
    <div className="space-y-4">
      {assets.map((asset) => (
        <motion.div
          key={asset.id}
          whileHover={{ y: -4, scale: 1.01 }}
          transition={{ duration: 0.2 }}
        >
          <Card
            className="cursor-pointer p-6 transition-all hover:border-cyan-400/40"
            onClick={() => navigate(`/assets/${asset.id}`)}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-5">
                <div className="rounded-xl bg-cyan-500/10 p-4 text-cyan-400">
                  {icon(asset.asset_type)}
                </div>

                <div>
                  <h2 className="text-xl font-semibold text-white">
                    {asset.name}
                  </h2>
                  <p className="mt-1 text-sm text-slate-400">
                    {asset.ip_address || "-"}
                  </p>
                  <p className="text-sm text-slate-500">{asset.asset_type}</p>
                </div>
              </div>

              <div className="flex items-center gap-8">
                <div>
                  <div className="text-xs uppercase text-slate-500">Owner</div>
                  <div className="text-white">{asset.owner || "-"}</div>
                </div>

                <div>
                  <div className="text-xs uppercase text-slate-500">
                    Environment
                  </div>
                  <div className="text-white">{asset.environment || "-"}</div>
                </div>

                <span
                  className={`rounded-full px-4 py-2 text-xs font-semibold ${badges[asset.criticality ?? "UNKNOWN"]}`}
                >
                  {asset.criticality ?? "UNKNOWN"}
                </span>

                <div className="flex gap-2" onClick={(e) => e.stopPropagation()}>
                  <ScanOptionsMenu
                    asset={asset}
                    scanning={scanningId === asset.id}
                    onScan={onScan}
                  />
                  <IconButton
                    label="Edit asset"
                    colorClass="bg-blue-600 hover:bg-blue-500"
                    onClick={() => onEdit(asset)}
                  >
                    <Pencil />
                  </IconButton>
                  <IconButton
                    label="Delete asset"
                    colorClass="bg-red-600 hover:bg-red-500"
                    onClick={() => onDelete(asset)}
                  >
                    <Trash2 />
                  </IconButton>
                </div>
              </div>
            </div>
          </Card>
        </motion.div>
      ))}
    </div>
  );
}
