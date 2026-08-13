import { useEffect, useState } from "react";

/**
 * Return the current epoch millisecond timestamp, refreshed on an interval.
 * Used to drive live elapsed time, ETA, and progress bars.
 *
 * When `enabled` is false the interval is paused and the last value is kept,
 * so inactive views stop re-rendering every tick.
 */
export function useNow(intervalMs = 1000, enabled = true): number {
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    if (!enabled) return;
    const id = window.setInterval(() => setNow(Date.now()), intervalMs);
    return () => window.clearInterval(id);
  }, [intervalMs, enabled]);

  return now;
}
