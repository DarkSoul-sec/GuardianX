import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import VirusTotalService from "@/services/virustotal";
import { QUERY_KEYS } from "@/shared/constants";
import type { VirusTotalResourceType } from "@/types/virustotal";

export function useVirusTotalLookup(
  type: VirusTotalResourceType,
  value: string
) {
  const normalized = value.trim();
  const enabled = normalized.length > 0;

  return useQuery({
    queryKey: [...QUERY_KEYS.virustotalLookup, type, normalized],
    queryFn: () => VirusTotalService.lookup(type, normalized),
    enabled,
    staleTime: 60_000,
  });
}

export function useVirusTotalStatus() {
  return useQuery({
    queryKey: QUERY_KEYS.virustotalStatus,
    queryFn: VirusTotalService.getStatus,
    staleTime: 30_000,
  });
}

export function useVirusTotalConnect() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (apiKey: string) => VirusTotalService.connect(apiKey),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.virustotalStatus });
    },
  });
}

export function useVirusTotalTest() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (apiKey?: string) => VirusTotalService.testConnection(apiKey),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.virustotalStatus });
    },
  });
}

export function useVirusTotalDisconnect() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => VirusTotalService.disconnect(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.virustotalStatus });
    },
  });
}
