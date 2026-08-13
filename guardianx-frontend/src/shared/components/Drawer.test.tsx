import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import Drawer from "@/shared/components/Drawer";

describe("Drawer", () => {
  it("renders nothing when closed", () => {
    render(<Drawer open={false}>content</Drawer>);
    expect(screen.queryByText("content")).not.toBeInTheDocument();
  });

  it("renders dialog semantics when open", () => {
    render(
      <Drawer open titleId="drawer-title">
        <h2 id="drawer-title">Title</h2>
      </Drawer>
    );
    const dialog = screen.getByRole("dialog");
    expect(dialog).toHaveAttribute("aria-modal", "true");
    expect(dialog).toHaveAttribute("aria-labelledby", "drawer-title");
    expect(screen.getByText("Title")).toBeInTheDocument();
  });

  it("closes on Escape", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(
      <Drawer open onClose={onClose}>
        <button>Inside</button>
      </Drawer>
    );

    await user.keyboard("{Escape}");
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("closes when the backdrop is clicked", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(
      <Drawer open onClose={onClose}>
        <button>Inside</button>
      </Drawer>
    );

    await user.click(screen.getByRole("dialog").parentElement!);
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
