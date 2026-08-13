import { useEffect, type RefObject } from "react";

/**
 * Calls `handler` when a pointer event occurs outside `ref`. Used by
 * dropdowns and popovers.
 */
export function useClickOutside(
  ref: RefObject<HTMLElement | null>,
  handler: () => void,
  enabled = true
): void {
  useEffect(() => {
    if (!enabled) return;

    function onPointerDown(event: PointerEvent) {
      const element = ref.current;
      if (!element) return;
      if (event.target instanceof Node && !element.contains(event.target)) {
        handler();
      }
    }

    document.addEventListener("pointerdown", onPointerDown);
    return () => document.removeEventListener("pointerdown", onPointerDown);
  }, [ref, handler, enabled]);
}

/**
 * Calls `handler` when the Escape key is pressed.
 */
export function useEscapeKey(handler: () => void, enabled = true): void {
  useEffect(() => {
    if (!enabled) return;

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") handler();
    }

    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [handler, enabled]);
}
