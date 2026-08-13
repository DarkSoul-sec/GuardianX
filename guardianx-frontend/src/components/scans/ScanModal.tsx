import { useEffect, useState } from "react";
import { Compass, Search, Play, Timer, Zap } from "lucide-react";

import { Button, Modal, Select } from "@/shared/components";
import { cn } from "@/shared/utils/cn";

import { useAssets } from "@/hooks/useAssets";
import { useStartScan } from "@/hooks/useScans";
import { useToastContext } from "@/hooks/useToastContext";
import { useDefaultScanProfile } from "@/shared/storage/defaultScanProfile";

import { SCAN_PROFILES } from "./scanProfiles";

import type { ScanProfile } from "@/types/scan";

interface Props {
  open: boolean;
  onClose: () => void;
}

const PROFILE_ICONS: Record<ScanProfile, React.ReactNode> = {
  standard: <Zap size={20} />,
  full: <Compass size={20} />,
};

export default function ScanModal({ open, onClose }: Props) {
  const { data: assets = [], isLoading: assetsLoading } = useAssets();
  const startScan = useStartScan();
  const { success, error } = useToastContext();

  const [assetId, setAssetId] = useState("");
  const [profile, setProfile] = useState<ScanProfile>("standard");
  const [defaultProfile] = useDefaultScanProfile();

  useEffect(() => {
    if (open) {
      setProfile(defaultProfile);
    }
  }, [open, defaultProfile]);

  function handleSubmit() {
    if (!assetId) {
      error("Please select an asset to scan.");
      return;
    }

    startScan.mutate(
      { asset_id: Number(assetId), scan_profile: profile },
      {
        onSuccess: () => {
          success("Scan launched. It will start shortly.");
          setAssetId("");
          setProfile("standard");
          onClose();
        },
        onError: () => {
          error("Failed to launch scan. Please try again.");
        },
      }
    );
  }

  return (
    <Modal open={open} onClose={onClose} titleId="scan-modal-title">
      <div className="p-8">
        <div className="mb-8 flex items-center gap-3">
          <Search className="text-cyan-400" size={34} />
          <div>
            <h2 id="scan-modal-title" className="text-3xl font-bold text-white">New Scan</h2>
            <p className="text-slate-400">
              Launch a security assessment against an asset
            </p>
          </div>
        </div>

        <p className="eyebrow mb-3">Target asset</p>
        {assetsLoading ? (
          <p className="py-6 text-slate-400">Loading assets...</p>
        ) : assets.length === 0 ? (
          <p className="py-6 text-slate-400">
            No assets available. Create an asset before running a scan.
          </p>
        ) : (
          <Select
            value={assetId}
            onChange={(e) => setAssetId(e.target.value)}
            aria-label="Select asset to scan"
          >
            <option value="">Select an asset</option>
            {assets.map((asset) => (
              <option key={asset.id} value={asset.id}>
                {asset.name} ({asset.ip_address || asset.domain || "no address"})
              </option>
            ))}
          </Select>
        )}

        <p className="eyebrow mb-3 mt-8">Scan coverage</p>
        <div className="grid gap-4 sm:grid-cols-2">
          {(Object.keys(SCAN_PROFILES) as ScanProfile[]).map((key) => {
            const meta = SCAN_PROFILES[key];
            const selected = profile === key;
            return (
              <button
                key={key}
                type="button"
                onClick={() => setProfile(key)}
                aria-pressed={selected}
                className={cn(
                  "flex flex-col rounded-2xl border p-4 text-left transition",
                  selected
                    ? "border-cyan-400/60 bg-cyan-500/10 shadow-[0_0_24px_rgba(34,211,238,0.15)]"
                    : "border-slate-800 bg-slate-900/60 hover:border-slate-600"
                )}
              >
                <div className="flex items-center gap-2">
                  <span
                    className={cn(
                      "rounded-lg p-2",
                      selected ? "bg-cyan-500/20 text-cyan-300" : "bg-slate-800 text-slate-400"
                    )}
                  >
                    {PROFILE_ICONS[key]}
                  </span>
                  <span className="font-semibold text-white">{meta.label}</span>
                </div>
                <p className="mt-3 text-xs leading-relaxed text-slate-400">
                  {meta.description}
                </p>
                <div className="mt-3 flex items-center gap-1.5 text-xs font-medium text-cyan-300">
                  <Timer size={13} />
                  Typical duration: {meta.duration}
                </div>
              </button>
            );
          })}
        </div>

        <div className="mt-8 flex justify-end gap-4">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!assetId || startScan.isPending}
          >
            <Play size={18} className="mr-2 inline" />
            {startScan.isPending ? "Starting..." : "Start Scan"}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
