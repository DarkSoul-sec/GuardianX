import api from "./api";
import type {
  NotificationItem,
  NotificationListResponse,
  UnreadCountResponse,
} from "@/types/notification";

class NotificationService {
  async getNotifications(limit = 20): Promise<NotificationListResponse> {
    const { data } = await api.get<NotificationListResponse>("/notifications", {
      params: { limit },
    });
    return data;
  }

  async getUnreadCount(): Promise<number> {
    const { data } = await api.get<UnreadCountResponse>("/notifications/unread-count");
    return data.unread;
  }

  async markRead(id: number): Promise<NotificationItem> {
    const { data } = await api.patch<NotificationItem>(
      `/notifications/${id}/read`
    );
    return data;
  }

  async markAllRead(): Promise<void> {
    await api.post("/notifications/read-all");
  }
}

const notificationService = new NotificationService();

export default notificationService;
