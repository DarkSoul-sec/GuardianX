import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import StatCard from "@/shared/components/StatCard";

describe("StatCard", () => {
  it("renders the label and formatted value", () => {
    render(<StatCard label="Assets" value={1234} />);
    expect(screen.getByText("Assets")).toBeInTheDocument();
    expect(screen.getByText("1,234")).toBeInTheDocument();
  });

  it("renders string values as-is with a suffix", () => {
    render(<StatCard label="Last Scan" value="Aug 5" suffix="/100" />);
    expect(screen.getByText("Aug 5")).toBeInTheDocument();
    expect(screen.getByText("/100")).toBeInTheDocument();
  });
});
