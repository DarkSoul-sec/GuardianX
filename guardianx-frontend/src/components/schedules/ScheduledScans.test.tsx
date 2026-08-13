import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { vi, describe, it, expect, beforeEach } from "vitest";

import type { ScheduledScan } from "@/types/schedule";

const schedules = vi.fn(() => [
  {
    id: 1,
    asset_id: 2,
    asset_name: "laptop",
    scanner: "nmap",
    cadence: "DAILY",
    time_of_day: "03:00",
    week_day: null,
    month_day: null,
    enabled: true,
    last_run_at: new Date(Date.now() - 3600_000).toISOString(),
    next_run_at: new Date(Date.now() + 3600_000).toISOString(),
    created_by: 1,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 2,
    asset_id: 4,
    asset_name: "oracle",
    scanner: "nmap",
    cadence: "WEEKLY",
    time_of_day: "06:30",
    week_day: "MON",
    month_day: null,
    enabled: false,
    last_run_at: null,
    next_run_at: new Date(Date.now() + 2 * 86_400_000).toISOString(),
    created_by: 1,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
] as ScheduledScan[]);

const updateMutate = vi.fn();
const runNowMutate = vi.fn();
const deleteMutate = vi.fn();

vi.mock("@/hooks/useSchedules", () => ({
  useSchedules: () => ({ data: schedules(), isLoading: false }),
  useCreateSchedule: () => ({ mutate: vi.fn(), isPending: false }),
  useUpdateSchedule: () => ({ mutate: updateMutate, isPending: false }),
  useRunScheduleNow: () => ({ mutate: runNowMutate, isPending: false }),
  useDeleteSchedule: () => ({ mutate: deleteMutate, isPending: false }),
}));

vi.mock("@/hooks/useToastContext", () => ({
  useToastContext: () => ({ success: vi.fn(), error: vi.fn() }),
}));

import ScheduledScans from "@/components/schedules/ScheduledScans";

function renderScans() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <ScheduledScans />
    </QueryClientProvider>
  );
}

describe("ScheduledScans", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the schedule rows with cadence and status badges", () => {
    renderScans();

    expect(screen.getByText("laptop")).toBeInTheDocument();
    expect(screen.getByText("oracle")).toBeInTheDocument();
    expect(screen.getByText("Daily at 03:00 UTC")).toBeInTheDocument();
    expect(screen.getByText("Monday at 06:30 UTC")).toBeInTheDocument();
    expect(screen.getByText("Active")).toBeInTheDocument();
    expect(screen.getByText("Paused")).toBeInTheDocument();
  });

  it("toggles a schedule on/off", async () => {
    const user = userEvent.setup();
    renderScans();

    const toggle = screen.getByRole("switch", {
      name: /pause schedule for laptop/i,
    });
    await user.click(toggle);

    expect(updateMutate).toHaveBeenCalledWith(
      { id: 1, dto: { enabled: false } },
      expect.anything()
    );
  });

  it("runs a schedule now and deletes a schedule", async () => {
    const user = userEvent.setup();
    renderScans();

    await user.click(
      screen.getAllByRole("button", { name: /run now/i })[1]
    );
    expect(runNowMutate).toHaveBeenCalledWith(2, expect.anything());

    await user.click(screen.getAllByRole("button", { name: /^delete/i })[1]);
    expect(deleteMutate).toHaveBeenCalledWith(2, expect.anything());
  });

  it("shows the empty state when there are no schedules", () => {
    schedules.mockReturnValue([]);

    renderScans();

    expect(screen.getByText("No scheduled scans")).toBeInTheDocument();
  });
});
