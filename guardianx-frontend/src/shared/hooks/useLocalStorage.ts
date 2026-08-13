import { useCallback, useEffect, useState } from "react";

/**
 * useState synced to localStorage. Falls back to memory storage when
 * localStorage is unavailable (SSR / restricted contexts).
 */
export function useLocalStorage<T>(
  key: string,
  initialValue: T
): [T, (value: T | ((previous: T) => T)) => void] {
  const [stored, setStored] = useState<T>(() => {
    try {
      const raw = window.localStorage.getItem(key);
      return raw !== null ? (JSON.parse(raw) as T) : initialValue;
    } catch {
      return initialValue;
    }
  });

  const setValue = useCallback(
    (value: T | ((previous: T) => T)) => {
      setStored((previous) => {
        const next = value instanceof Function ? value(previous) : value;
        try {
          window.localStorage.setItem(key, JSON.stringify(next));
        } catch {
          // Ignore storage failures (quota / private mode).
        }
        return next;
      });
    },
    [key]
  );

  useEffect(() => {
    function onStorage(event: StorageEvent) {
      if (event.key !== key) return;
      try {
        setStored(event.newValue ? (JSON.parse(event.newValue) as T) : initialValue);
      } catch {
        setStored(initialValue);
      }
    }

    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, [key, initialValue]);

  return [stored, setValue];
}
