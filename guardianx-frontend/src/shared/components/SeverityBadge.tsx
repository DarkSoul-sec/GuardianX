import Badge from "./Badge";

import type { SeverityLevel } from "@/theme";

interface Props {
  severity: string;
}

const colorMap: Record<SeverityLevel, "red" | "orange" | "yellow" | "green" | "gray"> = {
  critical: "red",
  high: "orange",
  medium: "yellow",
  low: "green",
  unknown: "gray",
};

export default function SeverityBadge({ severity }: Props) {
  const key = severity.toLowerCase() as SeverityLevel;

  return <Badge color={colorMap[key] ?? "gray"}>{severity}</Badge>;
}
