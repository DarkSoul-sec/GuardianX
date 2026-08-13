import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import Modal from "@/shared/components/Modal";

function Content() {
  return (
    <div>
      <button>First</button>
      <button>Second</button>
    </div>
  );
}

describe("Modal", () => {
  it("renders nothing when closed", () => {
    render(<Modal open={false}>content</Modal>);
    expect(screen.queryByText("content")).not.toBeInTheDocument();
  });

  it("renders content and dialog semantics when open", () => {
    render(
      <Modal open titleId="modal-title">
        <h2 id="modal-title">Title</h2>
        <p>content</p>
      </Modal>
    );
    const dialog = screen.getByRole("dialog");
    expect(dialog).toBeInTheDocument();
    expect(dialog).toHaveAttribute("aria-modal", "true");
    expect(dialog).toHaveAttribute("aria-labelledby", "modal-title");
  });

  it("closes on Escape", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(
      <Modal open onClose={onClose}>
        <Content />
      </Modal>
    );

    await user.keyboard("{Escape}");
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("focuses the first focusable element on open", () => {
    render(
      <Modal open>
        <Content />
      </Modal>
    );
    expect(screen.getByRole("button", { name: "First" })).toHaveFocus();
  });

  it("restores focus to the previously focused element on close", () => {
    const onClose = vi.fn();
    function Harness({ open }: { open: boolean }) {
      return (
        <>
          <button>Trigger</button>
          <Modal open={open} onClose={onClose}>
            <Content />
          </Modal>
        </>
      );
    }

    const { rerender } = render(<Harness open={false} />);
    const trigger = screen.getByRole("button", { name: "Trigger" });
    trigger.focus();

    rerender(<Harness open />);
    const dialog = screen.getByRole("dialog");
    expect(dialog).toContainElement(document.activeElement as HTMLElement);

    rerender(<Harness open={false} />);
    expect(trigger).toHaveFocus();
  });

  it("traps focus within the dialog", async () => {
    const user = userEvent.setup();
    render(
      <>
        <button>Outside in DOM</button>
        <Modal open>
          <Content />
        </Modal>
      </>
    );

    expect(screen.getByRole("button", { name: "First" })).toHaveFocus();
    await user.tab();
    expect(screen.getByRole("button", { name: "Second" })).toHaveFocus();
    await user.tab();
    expect(screen.getByRole("button", { name: "First" })).toHaveFocus();
    await user.tab({ shift: true });
    expect(screen.getByRole("button", { name: "Second" })).toHaveFocus();
  });

  it("closes when the backdrop is clicked", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(
      <Modal open onClose={onClose}>
        <Content />
      </Modal>
    );

    await user.click(screen.getByRole("dialog").parentElement!);
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
