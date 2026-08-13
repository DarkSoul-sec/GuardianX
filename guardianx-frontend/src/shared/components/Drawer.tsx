import {
  useEffect,
  useRef,
  type KeyboardEvent,
  type ReactNode,
} from "react";
import { motion } from "framer-motion";

import { cn } from "@/shared/utils/cn";

interface Props {
  open: boolean;
  children: ReactNode;
  onClose?: () => void;
  titleId?: string;
  panelClassName?: string;
}

const FOCUSABLE_SELECTOR = [
  "a[href]",
  "button:not([disabled])",
  "input:not([disabled])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  '[tabindex]:not([tabindex="-1"])',
].join(",");

export default function Drawer({
  open,
  children,
  onClose,
  titleId,
  panelClassName,
}: Props) {
  const panelRef = useRef<HTMLDivElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!open) return;

    previousFocusRef.current = document.activeElement as HTMLElement | null;
    document.body.style.overflow = "hidden";

    const panel = panelRef.current;
    const firstFocusable =
      panel?.querySelector<HTMLElement>(FOCUSABLE_SELECTOR);

    if (firstFocusable) {
      firstFocusable.focus();
    } else {
      panel?.focus();
    }

    return () => {
      document.body.style.overflow = "";
      previousFocusRef.current?.focus();
    };
  }, [open]);

  function handleKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === "Escape" && onClose) {
      event.stopPropagation();
      onClose();
    }

    if (event.key !== "Tab") return;

    const panel = panelRef.current;
    if (!panel) return;

    const focusable = Array.from(
      panel.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR)
    );
    if (focusable.length === 0) return;

    const first = focusable[0];
    const last = focusable[focusable.length - 1];

    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm"
      onClick={onClose}
    >
      <motion.div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        initial={{ x: 700 }}
        animate={{ x: 0 }}
        transition={{ duration: 0.35 }}
        onKeyDown={handleKeyDown}
        onClick={(e) => e.stopPropagation()}
        className={cn(
          "absolute right-0 h-full w-full max-w-[680px] overflow-y-auto border-l border-slate-800/70 bg-slate-950/80 p-8 text-white shadow-raised outline-none backdrop-blur-xl",
          panelClassName
        )}
      >
        {children}
      </motion.div>
    </div>
  );
}
