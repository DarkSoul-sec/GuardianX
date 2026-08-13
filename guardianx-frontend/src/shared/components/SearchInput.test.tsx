import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import SearchInput from "@/shared/components/SearchInput";

describe("SearchInput", () => {
  it("renders an input with an accessible label", () => {
    render(
      <SearchInput value="" onChange={() => undefined} ariaLabel="Search assets" />
    );
    expect(screen.getByRole("textbox", { name: "Search assets" })).toBeInTheDocument();
  });

  it("calls onChange when the value changes", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<SearchInput value="" onChange={onChange} />);

    await user.type(screen.getByRole("textbox", { name: "Search" }), "abc");
    expect(onChange).toHaveBeenCalledTimes(3);
  });

  it("shows a decorative search icon", () => {
    render(<SearchInput value="" onChange={() => undefined} />);
    expect(document.querySelector("svg")).toBeInTheDocument();
  });
});
