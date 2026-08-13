import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  type ReactNode,
  type RefObject,
} from "react";
import { createPortal } from "react-dom";

import { cn } from "@/shared/utils/cn";

interface PopoverProps {
  open: boolean;
  anchorRef: RefObject<HTMLElement | null>;
  onClose: () => void;
  children: ReactNode;
  align?: "start" | "center" | "end";
  offset?: number;
  viewportMargin?: number;
  className?: string;
  role?: string;
  ariaLabel?: string;
}

interface Position {
  top: number;
  left: number;
  width?: number;
}

/**
 * Portal-based popover that stays anchored to its trigger element.
 *
 * Renders into `document.body` so it can never be clipped by `overflow`
 * or trapped inside a parent stacking context. Position is measured from
 * the trigger's bounding rect and kept inside the visible viewport:
 *
 * - Opens below the trigger and flips above when there is not enough room.
 * - Clamps horizontally so the popover never extends past the right edge.
 * - Shrinks to fit on narrow screens instead of overflowing.
 * - Repositions while the page scrolls or the window is resized.
 */
export default function Popover({
  open,
  anchorRef,
  onClose,
  children,
  align = "end",
  offset = 8,
  viewportMargin = 8,
  className = "",
  role,
  ariaLabel,
}: PopoverProps) {
  const contentRef = useRef<HTMLDivElement>(null);
  const [position, setPosition] = useState<Position | null>(null);

  const updatePosition = useCallback(() => {
    const anchor = anchorRef.current;
    const content = contentRef.current;
    if (!anchor || !content) return;

    const anchorRect = anchor.getBoundingClientRect();
    const contentRect = content.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    const contentWidth = contentRect.width || content.offsetWidth || 0;
    const contentHeight = contentRect.height || content.offsetHeight || 0;

    const spaceBelow = viewportHeight - anchorRect.bottom - offset;
    const spaceAbove = anchorRect.top - offset;
    const placeBelow = spaceBelow >= contentHeight || spaceBelow >= spaceAbove;

    const top = placeBelow
      ? anchorRect.bottom + offset
      : Math.max(viewportMargin, anchorRect.top - offset - contentHeight);

    let left =
      align === "start"
        ? anchorRect.left
        : align === "center"
          ? anchorRect.left + anchorRect.width / 2 - contentWidth / 2
          : anchorRect.right - contentWidth;

    const maxWidth = Math.max(0, viewportWidth - viewportMargin * 2);
    let width: number | undefined;
    if (contentWidth > maxWidth) {
      width = maxWidth;
      left = viewportMargin;
    } else {
      left = Math.min(
        Math.max(viewportMargin, left),
        viewportWidth - viewportMargin - contentWidth
      );
    }

    setPosition({
      top: Math.max(viewportMargin, top),
      left: Math.max(viewportMargin, left),
      width,
    });
  }, [align, anchorRef, offset, viewportMargin]);

  useLayoutEffect(() => {
    if (!open) return;
    updatePosition();
  }, [open, updatePosition]);

  useEffect(() => {
    if (!open) return;

    function onScroll() {
      updatePosition();
    }
    function onResize() {
      updatePosition();
    }

    window.addEventListener("scroll", onScroll, true);
    window.addEventListener("resize", onResize);
    window.visualViewport?.addEventListener("scroll", onScroll);
    window.visualViewport?.addEventListener("resize", onResize);

    return () => {
      window.removeEventListener("scroll", onScroll, true);
      window.removeEventListener("resize", onResize);
      window.visualViewport?.removeEventListener("scroll", onScroll);
      window.visualViewport?.removeEventListener("resize", onResize);
    };
  }, [open, updatePosition]);

  useEffect(() => {
    if (!open) return;

    function handlePointerDown(event: PointerEvent) {
      const target = event.target as Node;
      if (anchorRef.current?.contains(target)) return;
      if (contentRef.current?.contains(target)) return;
      onClose();
    }

    document.addEventListener("pointerdown", handlePointerDown);
    return () => document.removeEventListener("pointerdown", handlePointerDown);
  }, [anchorRef, onClose, open]);

  useEffect(() => {
    if (!open) return;

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.stopPropagation();
        onClose();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onClose, open]);

  if (!open) return null;

  return createPortal(
    <div
      ref={contentRef}
      role={role}
      aria-label={ariaLabel}
      className={cn(
        "fixed z-50 rounded-2xl border border-slate-700 bg-slate-900 shadow-2xl shadow-black/60",
        className
      )}
      style={{
        top: position?.top ?? 0,
        left: position?.left ?? 0,
        width: position?.width,
        visibility: position ? "visible" : "hidden",
      }}
    >
      {children}
    </div>,
    document.body
  );
}
