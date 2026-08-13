import { Badge } from "@/shared/components";

import type { VirusTotalConnectionState } from "@/types/virustotal";

const CONFIG: Record<
  VirusTotalConnectionState,
  { label: string; color: "green" | "red" | "yellow" | "orange" | "gray" }
> = {
  connected: { label: "Connected", color: "green" },
  invalid: { label: "Invalid Key", color: "red" },
  rate_limited: { label: "Rate Limited", color: "yellow" },
  unreachable: { label: "Unreachable", color: "orange" },
  not_configured: { label: "Not Configured", color: "gray" },
};

interface Props {
  state: VirusTotalConnectionState;
}

export default function VirusTotalConnectionPill({ state }: Props) {
  const { label, color } = CONFIG[state];

  return <Badge color={color}>{label}</Badge>;
}
