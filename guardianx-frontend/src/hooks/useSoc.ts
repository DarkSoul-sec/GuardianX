import { useEffect } from "react";
import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  createIncident,
  deleteIncident,
  getActivity,
  getAlerts,
  getIncidents,
  getLoginHistory,
  getScanHealth,
  getSocOverview,
  updateAlertStatus,
  updateIncident,
} from "@/services/soc";
import { API_BASE_URL, QUERY_KEYS, STORAGE_KEYS } from "@/shared/constants";

export function useSocOverview() {
  return useQuery({
    queryKey: QUERY_KEYS.socOverview,
    queryFn: getSocOverview,
    refetchInterval: 15000,
  });
}

export function useScanHealth(days = 14) {
  return useQuery({
    queryKey: [...QUERY_KEYS.socScanHealth, days],
    queryFn: () => getScanHealth(days),
    refetchInterval: 60000,
  });
}

export function useAlerts(filters: { status?: string; severity?: string } = {}) {
  return useQuery({
    queryKey: [QUERY_KEYS.socAlerts, filters],
    queryFn: () => getAlerts(filters),
    refetchInterval: 60000,
  });
}

export function useIncidents(filters: { status?: string; severity?: string } = {}) {
  return useQuery({
    queryKey: [QUERY_KEYS.socIncidents, filters],
    queryFn: () => getIncidents(filters),
    refetchInterval: 60000,
  });
}

export function useActivity(limit = 50) {
  return useQuery({
    queryKey: [QUERY_KEYS.activity, limit],
    queryFn: () => getActivity(limit),
  });
}

export function useLoginHistory(limit = 20) {
  return useQuery({
    queryKey: [QUERY_KEYS.activityLogins, limit],
    queryFn: () => getLoginHistory(limit),
  });
}

export function useUpdateAlertStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) =>
      updateAlertStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.socAlerts });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.socOverview });
    },
  });
}

export function useCreateIncident() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createIncident,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.socIncidents });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.socAlerts });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.socOverview });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.activity });
    },
  });
}

export function useUpdateIncident() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Parameters<typeof updateIncident>[1] }) =>
      updateIncident(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.socIncidents });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.socOverview });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.activity });
    },
  });
}

export function useDeleteIncident() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteIncident,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.socIncidents });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.socOverview });
    },
  });
}

/**
 * Subscribe to realtime activity events and refresh the SOC feeds.
 */
export function useSocRealtime() {
  const queryClient = useQueryClient();

  useEffect(() => {
    const token = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
    if (!token) return;

    const wsBase = API_BASE_URL.replace(/^http/, "ws");
    const url = `${wsBase}/soc/alerts/ws?token=${encodeURIComponent(token)}`;

    let socket: WebSocket | null = null;

    try {
      socket = new WebSocket(url);
    } catch {
      return;
    }

    socket.onmessage = () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.socAlerts });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.socOverview });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.activity });
    };

    return () => {
      socket?.close();
    };
  }, [queryClient]);
}