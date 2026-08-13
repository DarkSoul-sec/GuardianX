import { useEffect } from "react";
import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import ScanService from "@/services/scans";
import { API_BASE_URL, QUERY_KEYS, STORAGE_KEYS } from "@/shared/constants";
import type { CreateScanDto, Scan } from "@/types/scan";

const ACTIVE_STATUSES = ["RUNNING", "PENDING"];

function isActiveScan(scan: Scan | undefined): boolean {
  return !!scan && ACTIVE_STATUSES.includes(scan.status);
}

export function useScans() {
  return useQuery({
    queryKey: QUERY_KEYS.scans,
    queryFn: ScanService.getScans,
    refetchInterval: (query) =>
      (query.state.data ?? []).some(isActiveScan) ? 15_000 : false,
  });
}

/**
 * Scan list with live WebSocket updates layered on top of the existing
 * polling. When the socket is unavailable the polling path is untouched.
 */
export function useScansRealtime() {
  const queryClient = useQueryClient();
  const query = useScans();

  useEffect(() => {
    const token = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
    if (!token) return;

    const wsBase = API_BASE_URL.replace(/^http/, "ws");
    const url = `${wsBase}/scans/ws?token=${encodeURIComponent(token)}`;

    let socket: WebSocket | null = null;

    try {
      socket = new WebSocket(url);
    } catch {
      return;
    }

    socket.onmessage = () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.scans });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.scanOperations });
    };

    socket.onclose = () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.scans });
    };

    return () => {
      socket?.close();
    };
  }, [queryClient]);

  return query;
}

export function useScanOperations() {
  return useQuery({
    queryKey: QUERY_KEYS.scanOperations,
    queryFn: ScanService.getScanOperations,
    refetchInterval: (query) => {
      const counts = query.state.data?.counts ?? {};
      const active = (counts.RUNNING ?? 0) + (counts.PENDING ?? 0);
      return active > 0 ? 5_000 : 30_000;
    },
  });
}

export function useScan(id: number) {
  return useQuery({
    queryKey: QUERY_KEYS.scan(id),
    queryFn: () => ScanService.getScan(id),
    enabled: !!id,
    refetchInterval: (query) => (isActiveScan(query.state.data) ? 10_000 : false),
  });
}

export function useScanResults(
  id: number,
  options?: { enabled?: boolean; refetchInterval?: number | false },
) {
  return useQuery({
    queryKey: QUERY_KEYS.scanResults(id),
    queryFn: () => ScanService.getScanResults(id),
    enabled: !!id && (options?.enabled ?? true),
    refetchInterval: options?.refetchInterval ?? false,
  });
}

export function useStartScan() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (dto: CreateScanDto) => ScanService.startScan(dto),

    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.scans });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.dashboard });
    },
  });
}

export function useCancelScan() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => ScanService.cancelScan(id),

    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.scans });
    },
  });
}
