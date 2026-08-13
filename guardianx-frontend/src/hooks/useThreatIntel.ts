import { useQuery } from "@tanstack/react-query";

import ThreatIntelService from "@/services/threat-intel";
import { QUERY_KEYS } from "@/shared/constants";
import type { ThreatIntelSearchFilters } from "@/types/threat-intel";

export function useThreatIntelStats(days: number) {
  return useQuery({
    queryKey: [...QUERY_KEYS.threatIntelStats, days],
    queryFn: () => ThreatIntelService.getStats(days),
    staleTime: 5 * 60_000,
  });
}

export function useThreatIntelTrending(days: number, limit: number) {
  return useQuery({
    queryKey: [...QUERY_KEYS.threatIntelTrending, days, limit],
    queryFn: () => ThreatIntelService.getTrending(days, limit),
    staleTime: 5 * 60_000,
  });
}

export function useThreatIntelSearch(
  filters: ThreatIntelSearchFilters,
  enabled: boolean
) {
  return useQuery({
    queryKey: [...QUERY_KEYS.threatIntelSearch, filters],
    queryFn: () => ThreatIntelService.search(filters),
    enabled,
    staleTime: 60_000,
  });
}

export function useThreatIntelCve(cveId: string | null) {
  return useQuery({
    queryKey: [...QUERY_KEYS.threatIntelCve, cveId],
    queryFn: () => ThreatIntelService.getCve(cveId as string),
    enabled: Boolean(cveId),
    staleTime: 5 * 60_000,
  });
}

export function useThreatIntelKev(limit: number) {
  return useQuery({
    queryKey: [...QUERY_KEYS.threatIntelKev, limit],
    queryFn: () => ThreatIntelService.getKev(limit),
    staleTime: 30 * 60_000,
  });
}
