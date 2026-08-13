import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import ScanOperationsStatus from "@/components/scans/ScanOperationsStatus";

import type { ScanOperations } from "@/types/scan";

function sampleOperations(
  overrides: Partial<ScanOperations> = {}
): ScanOperations {
  return {
    executor: {
      max_workers: 4,
      queued: 2,
      running: 2,
      idle_workers: 2,
      closed: false,
    },
    counts: {
      PENDING: 1,
      RUNNING: 2,
      COMPLETED: 10,
      FAILED: 1,
      CANCELLED: 3,
    },
    total: 17,
    ...overrides,
  };
}

function cardValue(label: string): HTMLElement | null {
  const labelNode = screen.getByText(label);
  return labelNode.closest("div")?.parentElement ?? null;
}

describe("ScanOperationsStatus", () => {
  it("renders worker pool and active/idle worker counts", () => {
    render(<ScanOperationsStatus data={sampleOperations()} />);

    expect(screen.getByText("Active Scans")).toBeInTheDocument();
    expect(screen.getByText("Worker Pool")).toBeInTheDocument();
    expect(screen.getByText("Workers Active")).toBeInTheDocument();
    expect(screen.getByText("Workers Idle")).toBeInTheDocument();

    expect(cardValue("Worker Pool")).toHaveTextContent("4");
    expect(cardValue("Workers Active")).toHaveTextContent("2");
    expect(cardValue("Workers Idle")).toHaveTextContent("2");
  });

  it("combines executor queued count with pending scheduler scans", () => {
    render(<ScanOperationsStatus data={sampleOperations()} />);
    expect(cardValue("Queued")).toHaveTextContent("3");
  });

  it("surfaces a scheduler hint when scans are pending", () => {
    render(<ScanOperationsStatus data={sampleOperations()} />);
    expect(screen.getByText("1 waiting in scheduler")).toBeInTheDocument();
  });

  it("shows skeletons while loading", () => {
    const { container } = render(
      <ScanOperationsStatus loading={true} data={undefined} />
    );
    expect(container.querySelectorAll(".animate-shimmer").length).toBe(5);
  });
});
