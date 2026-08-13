import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import FindingStats from "@/components/findings/FindingStats";

import type { FindingStats as FindingStatsType } from "@/types/finding";

vi.mock("@/hooks/useFindings", () => ({
  useFindingsStats: () => ({
    data: {
      total: 10,
      open: 5,
      in_progress: 2,
      resolved: 2,
      false_positive: 1,
      accepted_risk: 0,
      by_severity: { CRITICAL: 1, HIGH: 2, MEDIUM: 5 },
    } as FindingStatsType,
    isLoading: false,
  }),
}));

function renderWithClient() {
  const client = new QueryClient();
  return render(
    <QueryClientProvider client={client}>
      <FindingStats />
    </QueryClientProvider>
  );
}

describe("FindingStats", () => {
  it("renders triage status cards with live counts", () => {
    renderWithClient();

    expect(screen.getByText("Open")).toBeInTheDocument();
    expect(screen.getByText("In Progress")).toBeInTheDocument();
    expect(screen.getByText("Resolved")).toBeInTheDocument();
    expect(screen.getByText("False Positive")).toBeInTheDocument();
    expect(screen.getByText("Accepted Risk")).toBeInTheDocument();
  });

  it("surfaces the critical/high review count as a hint", () => {
    renderWithClient();
    expect(screen.getByText("3 critical/high need review")).toBeInTheDocument();
  });

  it("shows the total scope in the accepted risk card", () => {
    renderWithClient();
    expect(screen.getByText("/ 10")).toBeInTheDocument();
  });
});
