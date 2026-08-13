import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import IntelligenceService, {
  type IntelligenceHistoryParams,
} from "@/services/intelligence";
import { QUERY_KEYS } from "@/shared/constants";

export function useIntelligenceLookup() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (value: string) => IntelligenceService.lookup(value),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.intelligenceHistory,
      });
    },
  });
}

export function useIntelligenceHistory(params: IntelligenceHistoryParams) {
  return useQuery({
    queryKey: [
      ...QUERY_KEYS.intelligenceHistory,
      params.iocType ?? "all",
      params.q ?? "",
      params.page ?? 1,
      params.limit ?? 10,
    ],
    queryFn: () => IntelligenceService.getHistory(params),
    staleTime: 15_000,
  });
}

export function useIntelligenceDeleteHistory() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => IntelligenceService.deleteHistory(id),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.intelligenceHistory,
      });
    },
  });
}

export function useIntelligenceClearHistory() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => IntelligenceService.clearHistory(),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.intelligenceHistory,
      });
    },
  });
}

export function useIntelligenceStatus() {
  return useQuery({
    queryKey: QUERY_KEYS.intelligenceStatus,
    queryFn: IntelligenceService.getStatus,
    staleTime: 30_000,
    retry: false,
  });
}
