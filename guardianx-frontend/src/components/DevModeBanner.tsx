import { ShieldAlert } from "lucide-react";

import { usePrivateNetworkScanningEnabled } from "@/hooks/useSecurity";

export default function DevModeBanner() {
  const { data } = usePrivateNetworkScanningEnabled();

  if (!data?.private_network_scanning_enabled) {
    return null;
  }

  return (
    <div
      role="status"
      aria-live="polite"
      className="flex items-center gap-3 border-b border-amber-500/40 bg-amber-500/10 px-4 py-2 text-amber-300"
    >
      <ShieldAlert size={16} className="shrink-0" />
      <p className="text-sm font-semibold">
        Development Mode
        <span className="mx-2 text-amber-500/60">·</span>
        <span className="font-normal text-amber-200/90">
          Private Network Scanning Enabled
        </span>
      </p>
    </div>
  );
}