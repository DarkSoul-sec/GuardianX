import type { IntelligenceVendorDetection } from "@/types/intelligence";

export type DetectionSortKey =
  | "engine"
  | "result"
  | "category"
  | "engine_version"
  | "update_date";

export type SortDirection = "asc" | "desc";

const CATEGORY_RANK: Record<string, number> = {
  malicious: 0,
  suspicious: 1,
  harmless: 2,
  undetected: 3,
  "type-unsupported": 4,
  timeout: 5,
  "confirmed-timeout": 6,
  failure: 7,
};

export function filterDetections(
  items: IntelligenceVendorDetection[],
  query: string
): IntelligenceVendorDetection[] {
  const needle = query.trim().toLowerCase();
  if (!needle) return items;

  return items.filter((item) =>
    [item.engine, item.result, item.category].some(
      (value) => value !== null && value.toLowerCase().includes(needle)
    )
  );
}

function compareValues(
  a: string | number | null,
  b: string | number | null
): number {
  if (a === null && b === null) return 0;
  if (a === null) return 1;
  if (b === null) return -1;
  if (typeof a === "number" && typeof b === "number") return a - b;
  return String(a).localeCompare(String(b), undefined, { sensitivity: "base" });
}

export function sortDetections(
  items: IntelligenceVendorDetection[],
  key: DetectionSortKey,
  direction: SortDirection
): IntelligenceVendorDetection[] {
  const multiplier = direction === "asc" ? 1 : -1;

  return [...items].sort((a, b) => {
    if (key === "category") {
      const rankA = CATEGORY_RANK[a.category] ?? 99;
      const rankB = CATEGORY_RANK[b.category] ?? 99;
      if (rankA !== rankB) return (rankA - rankB) * multiplier;
    }

    return compareValues(a[key], b[key]) * multiplier;
  });
}
