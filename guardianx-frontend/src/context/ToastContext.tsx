import {
  useCallback,
  useState,
  type ReactNode,
} from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle2, XCircle, Info, X } from "lucide-react";

import { cn } from "@/shared/utils/cn";
import { ToastContext } from "@/hooks/useToastContext";

type ToastKind = "success" | "error" | "info";

interface Toast {
  id: number;
  kind: ToastKind;
  message: string;
}

const kindStyles: Record<ToastKind, { border: string; icon: ReactNode }> = {
  success: { border: "border-l-emerald-500", icon: <CheckCircle2 size={18} className="text-emerald-400" /> },
  error: { border: "border-l-red-500", icon: <XCircle size={18} className="text-red-400" /> },
  info: { border: "border-l-cyan-500", icon: <Info size={18} className="text-cyan-400" /> },
};

let nextId = 0;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const dismiss = useCallback((id: number) => {
    setToasts((previous) => previous.filter((toast) => toast.id !== id));
  }, []);

  const push = useCallback(
    (kind: ToastKind, message: string) => {
      const id = ++nextId;
      setToasts((previous) => [...previous, { id, kind, message }]);
      window.setTimeout(() => dismiss(id), 4000);
    },
    [dismiss]
  );

  const success = useCallback((message: string) => push("success", message), [push]);
  const error = useCallback((message: string) => push("error", message), [push]);
  const info = useCallback((message: string) => push("info", message), [push]);

  return (
    <ToastContext.Provider value={{ success, error, info }}>
      {children}

      <div
        aria-live="polite"
        className="pointer-events-none fixed right-4 top-4 z-[100] flex w-80 flex-col gap-3"
      >
        <AnimatePresence>
          {toasts.map((toast) => (
            <motion.div
              key={toast.id}
              initial={{ opacity: 0, x: 40 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 40 }}
              transition={{ duration: 0.2 }}
              className={cn(
                "pointer-events-auto flex items-start gap-3 rounded-xl border border-slate-800 border-l-4 bg-slate-900 p-4 shadow-lg",
                kindStyles[toast.kind].border
              )}
            >
              <div className="mt-0.5">{kindStyles[toast.kind].icon}</div>
              <p className="flex-1 text-sm text-slate-200">{toast.message}</p>
              <button
                onClick={() => dismiss(toast.id)}
                aria-label="Dismiss notification"
                className="text-slate-500 transition hover:text-slate-300"
              >
                <X size={16} />
              </button>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
}
