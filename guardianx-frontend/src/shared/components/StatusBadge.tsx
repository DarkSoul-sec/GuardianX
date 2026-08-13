import Badge from "./Badge";

import type { StatusLevel } from "@/theme";

interface Props {
  status: string;
}

const colorMap: Record<
  StatusLevel,
  "red" | "orange" | "yellow" | "green" | "cyan" | "blue" | "gray"
> = {
  pending: "gray",
  running: "cyan",
  completed: "green",
  failed: "red",
  cancelled: "gray",
  open: "red",
  inProgress: "yellow",
  resolved: "green",
  falsePositive: "gray",
  acceptedRisk: "blue",
};

export default function StatusBadge({ status }: Props) {
  const key = status.replace("-", "_").toLowerCase() as StatusLevel;

  return <Badge color={colorMap[key] ?? "gray"}>{status.replace("_", " ")}</Badge>;
}
