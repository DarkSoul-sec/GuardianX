import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import Badge from "@/shared/components/Badge";
import EmptyState from "@/shared/components/EmptyState";

describe("Badge", () => {
  it("renders its label", () => {
    render(<Badge>CRITICAL</Badge>);
    expect(screen.getByText("CRITICAL")).toBeInTheDocument();
  });
});

describe("EmptyState", () => {
  it("renders title and description", () => {
    render(
      <EmptyState
        title="No Assets Found"
        description="Create an asset to begin."
      />
    );
    expect(screen.getByText("No Assets Found")).toBeInTheDocument();
    expect(screen.getByText("Create an asset to begin.")).toBeInTheDocument();
  });
});
