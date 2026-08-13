import type {
  IntelligenceThreatLevel,
} from "@/types/intelligence";

export type BadgeColor =
  | "red"
  | "orange"
  | "yellow"
  | "green"
  | "cyan"
  | "blue"
  | "gray"
  | "amber";

export const THREAT_LEVEL_META: Record<
  IntelligenceThreatLevel,
  { label: string; color: BadgeColor }
> = {
  critical: { label: "Critical", color: "red" },
  high: { label: "High", color: "orange" },
  medium: { label: "Medium", color: "yellow" },
  low: { label: "Low", color: "cyan" },
  clean: { label: "Clean", color: "green" },
  unknown: { label: "Unknown", color: "gray" },
};

const CATEGORY_COLORS: Record<string, BadgeColor> = {
  malicious: "red",
  suspicious: "yellow",
  harmless: "green",
  clean: "green",
  undetected: "gray",
};

export function categoryColor(category: string): BadgeColor {
  return CATEGORY_COLORS[category.toLowerCase()] ?? "gray";
}
