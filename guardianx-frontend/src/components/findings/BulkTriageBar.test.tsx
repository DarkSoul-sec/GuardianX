import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import BulkTriageBar from "@/components/findings/BulkTriageBar";

const mutate = vi.fn();

vi.mock("@/hooks/useFindings", () => ({
  useBulkUpdateFindingStatus: () => ({
    mutate,
    isPending: false,
  }),
}));

vi.mock("@/hooks/useToastContext", () => ({
  useToastContext: () => ({
    success: vi.fn(),
    error: vi.fn(),
  }),
}));

function renderWithClient(ids: number[]) {
  const client = new QueryClient();
  return render(
    <QueryClientProvider client={client}>
      <BulkTriageBar selectedIds={ids} onClear={vi.fn()} />
    </QueryClientProvider>
  );
}

describe("BulkTriageBar", () => {
  beforeEach(() => {
    mutate.mockReset();
  });

  it("is hidden when nothing is selected", () => {
    const { container } = renderWithClient([]);
    expect(container.firstChild).toBeNull();
  });

  it("shows the selected count and applies a status", async () => {
    const user = userEvent.setup();
    renderWithClient([1, 2, 3]);

    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText(/selected/)).toBeInTheDocument();

    await user.selectOptions(screen.getByLabelText("Bulk status"), "RESOLVED");
    await user.click(screen.getByRole("button", { name: "Apply" }));

    expect(mutate).toHaveBeenCalledWith(
      { ids: [1, 2, 3], status: "RESOLVED" },
      expect.anything()
    );
  });
});
