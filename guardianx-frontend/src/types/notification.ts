export interface NotificationItem {
  id: number;
  user_id: number;
  notification_type: string;
  title: string;
  body: string | null;
  severity: string | null;
  finding_id: number | null;
  read_at: string | null;
  created_at: string;
}

export interface NotificationListResponse {
  items: NotificationItem[];
  total: number;
  unread: number;
}

export interface UnreadCountResponse {
  unread: number;
}
