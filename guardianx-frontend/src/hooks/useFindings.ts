import { useEffect } from "react";
import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import FindingService from "@/services/findings";
import { API_BASE_URL, QUERY_KEYS, STORAGE_KEYS } from "@/shared/constants";
import type {
  FindingQueryParams,
  FindingStatus,
  FindingTriageUpdate,
} from "@/types/finding";

export function useFindings(params?: FindingQueryParams) {
  return useQuery({
    queryKey: [QUERY_KEYS.findings[0], params],
    queryFn: () => FindingService.getFindings(params),
    placeholderData: (previous) => previous,
  });
}

export function useFinding(id: number) {
  return useQuery({
    queryKey: QUERY_KEYS.finding(id),
    queryFn: () => FindingService.getFinding(id),
    enabled: !!id,
  });
}

export function useFindingIntelligence(id: number, enabled: boolean) {
  return useQuery({
    queryKey: ["finding-intelligence", id],
    queryFn: () => FindingService.getFindingIntelligence(id),
    enabled: Boolean(id) && enabled,
    refetchInterval: (query) =>
      query.state.data?.status === "pending" ? 1_000 : false,
  });
}

export function useFindingsStats() {
  return useQuery({
    queryKey: QUERY_KEYS.findingStats,
    queryFn: FindingService.getFindingStats,
    refetchInterval: 30_000,
  });
}

export function useFindingActivities(id: number) {
  return useQuery({
    queryKey: QUERY_KEYS.findingActivities(id),
    queryFn: () => FindingService.getFindingActivities(id),
    enabled: !!id,
  });
}

export function useFindingsAssignees() {
  return useQuery({
    queryKey: QUERY_KEYS.findingAssignees,
    queryFn: FindingService.getAssignees,
    staleTime: 60_000,
  });
}

export function useUpdateFindingStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, status }: { id: number; status: FindingStatus }) =>
      FindingService.updateStatus(id, status),

    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.findings });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.finding(data.id) });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.findingStats });
    },
  });
}

export function useUpdateFindingTriage() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      payload,
    }: {
      id: number;
      payload: FindingTriageUpdate;
    }) => FindingService.updateTriage(id, payload),

    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.findings });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.finding(data.id) });
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.findingActivities(data.id),
      });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.findingStats });
    },
  });
}

export function useBulkUpdateFindingStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      ids,
      status,
    }: {
      ids: number[];
      status: FindingStatus;
    }) => FindingService.bulkUpdateStatus({ ids, status }),

    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.findings });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.findingStats });

      data.ids.forEach((id) => {
        queryClient.invalidateQueries({ queryKey: QUERY_KEYS.finding(id) });
      });
    },
  });
}

export function useExportFindings() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (params?: FindingQueryParams) =>
      FindingService.exportFindings(params),

    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.findings });
    },
  });
}

/**
 * Findings list with live WebSocket updates layered on top of the
 * existing query invalidation triggered by the triage mutations.
 */
export function useFindingsRealtime() {
  const queryClient = useQueryClient();

  useEffect(() => {
    const token = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
    if (!token) return;

    const wsBase = API_BASE_URL.replace(/^http/, "ws");
    const url = `${wsBase}/findings/ws?token=${encodeURIComponent(token)}`;

    let socket: WebSocket | null = null;

    try {
      socket = new WebSocket(url);
    } catch {
      return;
    }

    socket.onmessage = () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.findings });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.findingStats });
    };

    socket.onclose = () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.findings });
    };

    return () => {
      socket?.close();
    };
  }, [queryClient]);
}
