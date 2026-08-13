import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import Pagination from "@/shared/components/Pagination";

describe("Pagination", () => {
  it("renders nothing when there is a single page", () => {
    render(<Pagination page={1} pages={1} onChange={() => undefined} />);
    expect(screen.queryByLabelText("Pagination")).not.toBeInTheDocument();
  });

  it("renders all page buttons for a small page count", () => {
    render(<Pagination page={2} pages={5} onChange={() => undefined} />);
    for (let p = 1; p <= 5; p++) {
      expect(screen.getByRole("button", { name: `Page ${p}` })).toBeInTheDocument();
    }
  });

  it("marks the current page with aria-current", () => {
    render(<Pagination page={3} pages={5} onChange={() => undefined} />);
    expect(screen.getByRole("button", { name: "Page 3" })).toHaveAttribute(
      "aria-current",
      "page"
    );
    expect(screen.getByRole("button", { name: "Page 1" })).not.toHaveAttribute(
      "aria-current"
    );
  });

  it("windows large page counts with ellipsis", () => {
    render(<Pagination page={10} pages={30} onChange={() => undefined} />);
    expect(screen.getByRole("button", { name: "Page 1" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Page 30" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Page 9" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Page 11" })).toBeInTheDocument();
    expect(screen.getAllByText("…")).not.toHaveLength(0);
  });

  it("calls onChange with the next page", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<Pagination page={2} pages={5} onChange={onChange} />);

    await user.click(screen.getByRole("button", { name: "Next" }));
    expect(onChange).toHaveBeenCalledWith(3);

    await user.click(screen.getByRole("button", { name: "Previous" }));
    expect(onChange).toHaveBeenCalledWith(1);
  });

  it("disables Previous on the first page and Next on the last", () => {
    render(<Pagination page={1} pages={2} onChange={() => undefined} />);
    expect(screen.getByRole("button", { name: "Previous" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Next" })).not.toBeDisabled();
  });
});
