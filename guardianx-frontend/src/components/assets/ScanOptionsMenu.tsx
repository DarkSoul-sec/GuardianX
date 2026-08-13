import { useRef, useState } from "react";
import { Loader2, Play, Timer, Zap, Compass } from "lucide-react";

import { IconButton, Popover } from "@/shared/components";
import { cn } from "@/shared/utils/cn";

import { SCAN_PROFILES } from "@/components/scans/scanProfiles";
import { useDefaultScanProfile } from "@/shared/storage/defaultScanProfile";

import type { Asset } from "@/types/asset";
import type { ScanProfile } from "@/types/scan";

const PROFILE_ICONS: Record<ScanProfile, React.ReactNode> = {
  standard: <Zap size={20} />,
  full: <Compass size={20} />,
};

interface Props {
  asset: Asset;
  scanning: boolean;
  onScan: (asset: Asset, profile: ScanProfile) => void;
}

export default function ScanOptionsMenu({ asset, scanning, onScan }: Props) {
  const [open, setOpen] = useState(false);
  const [defaultProfile] = useDefaultScanProfile();
  const anchorRef = useRef<HTMLDivElement>(null);

  function handleSelect(profile: ScanProfile) {
    setOpen(false);
    onScan(asset, profile);
  }

  return (
    <div ref={anchorRef} className="relative">
      <IconButton
        label="Run scan"
        aria-haspopup="menu"
        aria-expanded={open}
        disabled={scanning}
        onClick={() => setOpen((value) => !value)}
        colorClass={cn(
          "bg-emerald-600 hover:bg-emerald-500",
          open && "bg-emerald-500 ring-2 ring-emerald-300/60"
        )}
      >
        {scanning ? <Loader2 className="animate-spin" /> : <Play />}
      </IconButton>

      <Popover
        open={open}
        anchorRef={anchorRef}
        onClose={() => setOpen(false)}
        align="end"
        offset={8}
        className="w-72 p-2"
        role="menu"
        ariaLabel={`Scan options for ${asset.name}`}
      >
        <p className="px-3 pb-2 pt-1 text-xs font-semibold uppercase tracking-wide text-slate-500">
          Scan coverage
        </p>
        {(Object.keys(SCAN_PROFILES) as ScanProfile[]).map((profile) => {
          const meta = SCAN_PROFILES[profile];
          const isDefault = defaultProfile === profile;
          return (
            <button
              key={profile}
              type="button"
              role="menuitem"
              onClick={() => handleSelect(profile)}
              className="flex w-full items-start gap-3 rounded-xl px-3 py-3 text-left transition hover:bg-slate-800"
            >
              <span className="mt-0.5 rounded-lg bg-slate-800 p-2 text-slate-300">
                {PROFILE_ICONS[profile]}
              </span>
              <span className="flex-1">
                <span className="flex items-center gap-2">
                  <span className="font-semibold text-white">
                    {meta.label}
                  </span>
                  {isDefault && (
                    <span className="rounded-full bg-cyan-500/20 px-2 py-0.5 text-[10px] font-semibold uppercase text-cyan-300">
                      Default
                    </span>
                  )}
                </span>
                <span className="mt-1 flex items-center gap-1.5 text-xs text-slate-400">
                  <Timer size={12} />
                  {meta.duration}
                </span>
              </span>
            </button>
          );
        })}
        <p className="px-3 py-2 text-[11px] leading-relaxed text-slate-500">
          Scans run in the background. Findings appear on the Scans and
          Dashboard pages when complete.
        </p>
      </Popover>
    </div>
  );
}
