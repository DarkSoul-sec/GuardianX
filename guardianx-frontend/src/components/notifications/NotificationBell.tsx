import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Bell, CheckCheck } from "lucide-react";

import { useMarkAllNotificationsRead, useMarkNotificationRead, useNotifications, useNotificationsRealtime, useUnreadCount } from "@/hooks/useNotifications";
import { formatRelativeTime } from "@/shared/utils/format";
import { cn } from "@/shared/utils/cn";

export default function NotificationBell() {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  const { data: unreadData } = useUnreadCount();
  const { data } = useNotifications();
  const markRead = useMarkNotificationRead();
  const markAllRead = useMarkAllNotificationsRead();

  useNotificationsRealtime();

  const unread = unreadData ?? data?.unread ?? 0;
  const items = data?.items ?? [];

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  function handleSelect(notification: (typeof items)[number]) {
    setOpen(false);

    if (notification.read_at === null) {
      markRead.mutate(notification.id);
    }

    if (notification.finding_id) {
      navigate(`/findings?q=${encodeURIComponent(notification.title)}`);
    }
  }

  return (
    <div ref={ref} className="relative">
      <button
        className="relative rounded-lg p-2 text-slate-300 transition hover:bg-slate-800 hover:text-white"
        aria-label={`Notifications (${unread} unread)`}
        title="Notifications"
        onClick={() => setOpen((previous) => !previous)}
      >
        <Bell size={20} />
        {unread > 0 && (
          <span className="absolute right-0.5 top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white">
            {unread > 9 ? "9+" : unread}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 z-50 mt-2 w-80 overflow-hidden rounded-2xl border border-slate-800 bg-slate-900 shadow-2xl">
          <div className="flex items-center justify-between border-b border-slate-800 px-4 py-3">
            <p className="font-semibold">Notifications</p>
            {unread > 0 && (
              <button
                className="flex items-center gap-1 text-xs text-cyan-400 transition hover:text-cyan-300"
                onClick={() => markAllRead.mutate()}
              >
                <CheckCheck size={14} />
                Mark all read
              </button>
            )}
          </div>

          {items.length === 0 ? (
            <p className="px-4 py-8 text-center text-sm text-slate-500">
              No notifications yet.
            </p>
          ) : (
            <ul className="max-h-80 overflow-y-auto">
              {items.map((notification) => {
                const isUnread = notification.read_at === null;

                return (
                  <li key={notification.id}>
                    <button
                      onClick={() => handleSelect(notification)}
                      className={cn(
                        "w-full border-b border-slate-800/60 px-4 py-3 text-left transition hover:bg-slate-800/50",
                        !isUnread && "opacity-60"
                      )}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <p className="text-sm font-semibold text-white">
                          {notification.title}
                        </p>
                        {isUnread && (
                          <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-cyan-400" />
                        )}
                      </div>
                      {notification.body && (
                        <p className="mt-1 text-xs text-slate-400">
                          {notification.body}
                        </p>
                      )}
                      <p className="mt-1 text-[10px] uppercase tracking-wide text-slate-500">
                        {formatRelativeTime(notification.created_at)}
                      </p>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
