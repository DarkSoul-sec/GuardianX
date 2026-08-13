import { useCallback, useSyncExternalStore } from "react";

import { SCAN_PROFILES } from "@/components/scans/scanProfiles";
import type { ScanProfile } from "@/types/scan";

const STORAGE_KEY = "guardianx_default_scan_profile";

function isScanProfile(value: string | null): value is ScanProfile {
  return value !== null && value in SCAN_PROFILES;
}

export function getDefaultScanProfile(): ScanProfile {
  if (typeof window === "undefined") return "standard";
  const stored = window.localStorage.getItem(STORAGE_KEY);
  return isScanProfile(stored) ? stored : "standard";
}

export function setDefaultScanProfile(profile: ScanProfile): void {
  window.localStorage.setItem(STORAGE_KEY, profile);
  listeners.forEach((listener) => listener());
}

const listeners = new Set<() => void>();

export function subscribeDefaultScanProfile(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function useDefaultScanProfile(): [
  ScanProfile,
  (profile: ScanProfile) => void,
] {
  const profile = useSyncExternalStore(
    subscribeDefaultScanProfile,
    getDefaultScanProfile
  );
  const setProfile = useCallback((next: ScanProfile) => {
    setDefaultScanProfile(next);
  }, []);
  return [profile, setProfile];
}
