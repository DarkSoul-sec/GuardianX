type ClassValue = string | number | null | undefined | false | Record<string, boolean> | ClassValue[];

/**
 * Tiny class-name joiner. Accepts strings and boolean maps.
 */
export function cn(...values: ClassValue[]): string {
  const parts: string[] = [];

  function append(value: ClassValue): void {
    if (!value) return;

    if (typeof value === "string" || typeof value === "number") {
      parts.push(String(value));
      return;
    }

    if (Array.isArray(value)) {
      for (const item of value) append(item);
      return;
    }

    if (typeof value === "object") {
      for (const [key, enabled] of Object.entries(value)) {
        if (enabled) parts.push(key);
      }
    }
  }

  for (const value of values) append(value);

  return parts.join(" ");
}
