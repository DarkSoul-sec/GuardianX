import { Compass, Timer, Zap } from "lucide-react";

import { Card } from "@/shared/components";
import { cn } from "@/shared/utils/cn";

import { SCAN_PROFILES } from "@/components/scans/scanProfiles";
import { useDefaultScanProfile } from "@/shared/storage/defaultScanProfile";

import type { ScanProfile } from "@/types/scan";

const PROFILE_ICONS: Record<ScanProfile, React.ReactNode> = {
  standard: <Zap size={20} />,
  full: <Compass size={20} />,
};

export default function ScanPreferencesCard() {
  const [defaultProfile, setDefaultProfile] = useDefaultScanProfile();

  return (
    <Card className="p-8">
      <h2 className="mb-2 text-2xl font-bold text-white">Scan Preferences</h2>
      <p className="mb-6 text-sm text-slate-400">
        Choose which scan coverage is pre-selected when starting a new scan.
      </p>

      <div className="grid gap-4 sm:grid-cols-2">
        {(Object.keys(SCAN_PROFILES) as ScanProfile[]).map((profile) => {
          const meta = SCAN_PROFILES[profile];
          const selected = defaultProfile === profile;
          return (
            <button
              key={profile}
              type="button"
              onClick={() => setDefaultProfile(profile)}
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
                    selected
                      ? "bg-cyan-500/20 text-cyan-300"
                      : "bg-slate-800 text-slate-400"
                  )}
                >
                  {PROFILE_ICONS[profile]}
                </span>
                <span className="font-semibold text-white">{meta.label}</span>
                {selected && (
                  <span className="ml-auto rounded-full bg-cyan-500/20 px-2 py-0.5 text-[10px] font-semibold uppercase text-cyan-300">
                    Default
                  </span>
                )}
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

      <p className="mt-6 text-xs leading-relaxed text-slate-500">
        Your default is used as the starting selection in the New Scan dialog
        and the quick scan menu on the Assets page. You can always pick a
        different coverage per scan.
      </p>
    </Card>
  );
}
