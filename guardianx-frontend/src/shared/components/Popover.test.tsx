import { describe, expect, it, vi } from "vitest";
import { useRef } from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import Popover from "@/shared/components/Popover";

function Harness({
  open,
  onClose,
}: {
  open: boolean;
  onClose?: () => void;
}) {
  const anchorRef = useRef<HTMLButtonElement>(null);
  return (
    <div>
      <button data-testid="outside">Outside</button>
      <button ref={anchorRef}>Trigger</button>
      <Popover open={open} anchorRef={anchorRef} onClose={onClose ?? vi.fn()}>
        <button>Popover content</button>
      </Popover>
    </div>
  );
}

describe("Popover", () => {
  it("renders nothing when closed", () => {
    render(<Harness open={false} />);
    expect(screen.queryByText("Popover content")).not.toBeInTheDocument();
  });

  it("renders content in a portal when open", () => {
    render(<Harness open />);
    expect(screen.getByText("Popover content")).toBeInTheDocument();
  });

  it("does not close when clicking the trigger or inside content", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(<Harness open onClose={onClose} />);

    await user.click(screen.getByText("Trigger"));
    expect(onClose).not.toHaveBeenCalled();

    await user.click(screen.getByText("Popover content"));
    expect(onClose).not.toHaveBeenCalled();
  });

  it("closes when clicking outside the trigger and content", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(<Harness open onClose={onClose} />);

    await user.click(screen.getByTestId("outside"));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("closes on Escape", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(<Harness open onClose={onClose} />);

    await user.keyboard("{Escape}");
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
