import { useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import NotificationService from "@/services/notifications";
import { API_BASE_URL, QUERY_KEYS, STORAGE_KEYS } from "@/shared/constants";

export function useNotifications(limit = 20) {
  return useQuery({
    queryKey: QUERY_KEYS.notifications,
    queryFn: () => NotificationService.getNotifications(limit),
    refetchInterval: 60_000,
  });
}

export function useUnreadCount() {
  return useQuery({
    queryKey: QUERY_KEYS.unreadCount,
    queryFn: NotificationService.getUnreadCount,
    refetchInterval: 60_000,
  });
}

export function useMarkNotificationRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => NotificationService.markRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.notifications });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.unreadCount });
    },
  });
}

export function useMarkAllNotificationsRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => NotificationService.markAllRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.notifications });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.unreadCount });
    },
  });
}

/**
 * Subscribe to the realtime notification stream and refresh the bell badge
 * whenever a new notification arrives.
 */
export function useNotificationsRealtime() {
  const queryClient = useQueryClient();

  useEffect(() => {
    const token = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
    if (!token) return;

    const wsBase = API_BASE_URL.replace(/^http/, "ws");
    const url = `${wsBase}/notifications/ws?token=${encodeURIComponent(token)}`;

    let socket: WebSocket | null = null;

    try {
      socket = new WebSocket(url);
    } catch {
      return;
    }

    socket.onmessage = () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.notifications });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.unreadCount });
    };

    return () => {
      socket?.close();
    };
  }, [queryClient]);
}
