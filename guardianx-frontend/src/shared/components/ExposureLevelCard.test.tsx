import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import ExposureLevelCard from "@/shared/components/ExposureLevelCard";

describe("ExposureLevelCard", () => {
  it("renders the exposure level badge", () => {
    render(<ExposureLevelCard score={70} internetFacing={true} />);
    expect(screen.getByText("Exposure Level")).toBeInTheDocument();
    expect(screen.getByText("CRITICAL")).toBeInTheDocument();
    expect(screen.getByText(/70/)).toBeInTheDocument();
    expect(screen.getByText("Internet facing")).toBeInTheDocument();
  });

  it("shows internal network for non-internet-facing assets", () => {
    render(<ExposureLevelCard score={10} internetFacing={false} />);
    expect(screen.getByText("LOW")).toBeInTheDocument();
    expect(screen.getByText("Internal network")).toBeInTheDocument();
  });
});
