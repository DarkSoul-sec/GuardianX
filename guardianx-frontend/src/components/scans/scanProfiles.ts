import type { ScanProfile } from "@/types/scan";

export interface ScanProfileMeta {
  label: string;
  shortLabel: string;
  description: string;
  duration: string;
  badge: "blue" | "amber";
}

export const SCAN_PROFILES: Record<ScanProfile, ScanProfileMeta> = {
  standard: {
    label: "Top 1000 Ports",
    shortLabel: "Top 1000",
    description:
      "Nmap's most common TCP ports plus version detection. Fast and covers the vast majority of exposed services.",
    duration: "~2-6 min",
    badge: "blue",
  },
  full: {
    label: "All 65,535 Ports",
    shortLabel: "Full Range",
    description:
      "Every TCP port (1-65535) plus version detection. Slow and network-heavy, but finds uncommon and high ports.",
    duration: "~15-60+ min",
    badge: "amber",
  },
};

export function getScanProfile(profile: ScanProfile): ScanProfileMeta {
  return SCAN_PROFILES[profile];
}
