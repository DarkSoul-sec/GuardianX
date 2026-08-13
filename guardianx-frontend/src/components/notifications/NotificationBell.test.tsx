import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { vi, describe, it, expect, beforeEach } from "vitest";
import type { NotificationListResponse } from "@/types/notification";

const notificationData = vi.fn<() => NotificationListResponse>(() => ({
  items: [
    {
      id: 1,
      user_id: 1,
      notification_type: "critical_finding",
      title: "Critical finding detected",
      body: "1 critical and 1 high",
      severity: "CRITICAL",
      finding_id: 42,
      read_at: null,
      created_at: new Date().toISOString(),
    },
    {
      id: 2,
      user_id: 1,
      notification_type: "assignment",
      title: "Finding assigned to you",
      body: "CVE-2024-0001",
      severity: "MEDIUM",
      finding_id: 43,
      read_at: "2026-08-06T00:00:00Z",
      created_at: new Date().toISOString(),
    },
  ],
  total: 2,
  unread: 1,
}));

const unreadData = vi.fn<() => number>(() => 1);

vi.mock("@/hooks/useNotifications", () => ({
  useNotifications: () => ({ data: notificationData(), isLoading: false }),
  useUnreadCount: () => ({ data: unreadData(), isLoading: false }),
  useNotificationsRealtime: () => {},
  useMarkNotificationRead: () => ({ mutate: vi.fn() }),
  useMarkAllNotificationsRead: () => ({ mutate: vi.fn() }),
}));

import NotificationBell from "@/components/notifications/NotificationBell";

function renderBell() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <NotificationBell />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

function renderAndReturnUnmount() {
  return renderBell().unmount;
}

describe("NotificationBell", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows an unread badge with the unread count", () => {
    renderBell();

    expect(screen.getByText("1")).toBeInTheDocument();
  });

  it("renders the notifications in the dropdown when opened", async () => {
    const user = userEvent.setup();
    renderBell();

    await user.click(screen.getByRole("button", { name: /notifications/i }));

    expect(screen.getByText("Critical finding detected")).toBeInTheDocument();
    expect(screen.getByText("Finding assigned to you")).toBeInTheDocument();
    expect(screen.getByText("Mark all read")).toBeInTheDocument();
  });

  it("hides mark-all-read when every notification has been read", async () => {
    const user = userEvent.setup();
    const unmount = renderAndReturnUnmount();
    await user.click(screen.getByRole("button", { name: /notifications/i }));
    expect(screen.getByText("Mark all read")).toBeInTheDocument();
    unmount();

    unreadData.mockReturnValue(0);
    notificationData.mockReturnValue({
      items: [
        {
          id: 2,
          user_id: 1,
          notification_type: "assignment",
          title: "Finding assigned to you",
          body: null,
          severity: null,
          finding_id: null,
          read_at: "2026-08-06T00:00:00Z",
          created_at: new Date().toISOString(),
        },
      ],
      total: 1,
      unread: 0,
    });

    renderBell();

    await user.click(screen.getByRole("button", { name: /notifications/i }));

    expect(screen.queryByText("Mark all read")).not.toBeInTheDocument();
  });
});
