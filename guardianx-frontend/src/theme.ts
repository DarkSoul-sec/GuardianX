/**
 * GuardianX Design System
 *
 * Single source of truth for visual tokens. Tailwind utilities are derived
 * from these values in `index.css` via `@theme`; the JavaScript exports are
 * used for charts, badges, and imperative styling that Tailwind cannot reach.
 */

/* ------------------------------------------------------------------ */
/* Base palette                                                       */
/* ------------------------------------------------------------------ */

export const colors = {
  background: {
    canvas: "#030616",
    surface: "#050a18",
    elevated: "#0b1226",
    overlay: "rgba(3, 6, 22, 0.7)",
  },
  surface: {
    default: "#0b1226",
    raised: "#131c38",
    muted: "#1e2a4d",
  },
  border: {
    subtle: "#131c38",
    default: "#33446e",
    strong: "#5b6b96",
  },
  text: {
    primary: "#f4f7fe",
    secondary: "#8ba0c8",
    muted: "#5b6b96",
    disabled: "#33446e",
  },
  primary: {
    50: "#ecfeff",
    100: "#cffafe",
    200: "#a5f3fc",
    300: "#7df5ff",
    400: "#38e0ff",
    500: "#00cfff",
    600: "#00a8d8",
    700: "#0083b3",
  },
  success: "#22e59a",
  warning: "#ffd23b",
  danger: "#ff3b5c",
  violet: "#8b5cf6",
} as const;

/* ------------------------------------------------------------------ */
/* Severity colors (findings / vulnerabilities)                       */
/* ------------------------------------------------------------------ */

export const severityColors = {
  critical: "#dc2626",
  high: "#ea580c",
  medium: "#ca8a04",
  low: "#16a34a",
  unknown: "#64748b",
} as const;

export type SeverityLevel = keyof typeof severityColors;

export const severityOrder: SeverityLevel[] = [
  "critical",
  "high",
  "medium",
  "low",
  "unknown",
];

/* ------------------------------------------------------------------ */
/* Status colors (scans + findings)                                   */
/* ------------------------------------------------------------------ */

export const statusColors = {
  pending: "#64748b",
  running: "#06b6d4",
  completed: "#16a34a",
  failed: "#dc2626",
  cancelled: "#64748b",
  open: "#dc2626",
  inProgress: "#ca8a04",
  resolved: "#16a34a",
  falsePositive: "#64748b",
  acceptedRisk: "#3b82f6",
} as const;

export type StatusLevel = keyof typeof statusColors;

export const statusOrder: StatusLevel[] = [
  "pending",
  "running",
  "completed",
  "failed",
  "open",
  "inProgress",
  "resolved",
  "falsePositive",
  "acceptedRisk",
];

export const findingStatusOrder: StatusLevel[] = [
  "open",
  "inProgress",
  "resolved",
  "falsePositive",
  "acceptedRisk",
];

export const scanStatusOrder: StatusLevel[] = [
  "pending",
  "running",
  "completed",
  "failed",
  "cancelled",
];

/* ------------------------------------------------------------------ */
/* Risk colors (risk scores 0-100)                                    */
/* ------------------------------------------------------------------ */

export const riskColors = {
  low: "#16a34a",
  medium: "#ca8a04",
  high: "#ea580c",
  critical: "#dc2626",
} as const;

/**
 * Map a 0-100 risk score to a semantic risk level.
 */
export function riskLevel(score: number): keyof typeof riskColors {
  if (score >= 75) return "critical";
  if (score >= 50) return "high";
  if (score >= 25) return "medium";
  return "low";
}

export function riskColor(score: number): string {
  return riskColors[riskLevel(score)];
}

export type ExposureLevel = "low" | "medium" | "high" | "critical";

const exposureOrder: ExposureLevel[] = [
  "low",
  "medium",
  "high",
  "critical",
];

/**
 * Derive a graded exposure level from the attack-surface score, raising it
 * one step when the asset is reachable from the internet.
 */
export function exposureLevel(
  attackSurfaceScore: number,
  internetFacing: boolean,
): ExposureLevel {
  const base = riskLevel(attackSurfaceScore);

  if (!internetFacing || base === "critical") {
    return base;
  }

  return exposureOrder[exposureOrder.indexOf(base) + 1] ?? "critical";
}

export function exposureColor(
  attackSurfaceScore: number,
  internetFacing: boolean,
): string {
  return riskColors[exposureLevel(attackSurfaceScore, internetFacing)];
}

/* ------------------------------------------------------------------ */
/* Spacing, radius, shadows, transitions, typography                  */
/* ------------------------------------------------------------------ */

export const spacing = {
  xs: "0.25rem", // 4
  sm: "0.5rem", // 8
  md: "0.75rem", // 12
  lg: "1rem", // 16
  xl: "1.5rem", // 24
  "2xl": "2rem", // 32
  "3xl": "3rem", // 48
} as const;

export const radius = {
  sm: "0.5rem",
  md: "0.75rem",
  lg: "1rem",
  xl: "1.25rem",
  full: "9999px",
} as const;

export const shadows = {
  sm: "0 1px 2px rgba(0, 0, 0, 0.2)",
  md: "0 4px 16px rgba(0, 0, 0, 0.45)",
  lg: "0 12px 40px rgba(0, 0, 0, 0.6)",
  xl: "0 24px 60px rgba(0, 0, 0, 0.7)",
  glow: "0 0 24px rgba(0, 207, 255, 0.35)",
  glowSoft: "0 0 12px rgba(0, 207, 255, 0.18)",
  glowViolet: "0 0 24px rgba(139, 92, 246, 0.35)",
} as const;

export const transitions = {
  fast: "150ms cubic-bezier(0.4, 0, 0.2, 1)",
  normal: "250ms cubic-bezier(0.4, 0, 0.2, 1)",
  slow: "400ms cubic-bezier(0.4, 0, 0.2, 1)",
} as const;

export const fontSizes = {
  xs: "0.75rem",
  sm: "0.875rem",
  base: "1rem",
  lg: "1.125rem",
  xl: "1.25rem",
  "2xl": "1.5rem",
  "3xl": "1.875rem",
  "4xl": "2.25rem",
  "5xl": "3rem",
} as const;

export const fonts = {
  display: "Orbitron, ui-sans-serif, system-ui, sans-serif",
  sans: "Rajdhani, Inter, system-ui, -apple-system, sans-serif",
  mono: "JetBrains Mono, ui-monospace, SFMono-Regular, Menlo, monospace",
} as const;

/* ------------------------------------------------------------------ */
/* Chart color sets                                                    */
/* ------------------------------------------------------------------ */

export const chartPalette = {
  cyan: "#06b6d4",
  blue: "#3b82f6",
  purple: "#8b5cf6",
  emerald: "#10b981",
  amber: "#f59e0b",
  rose: "#f43f5e",
} as const;

export const severityChartColors: Record<SeverityLevel, string> = {
  critical: severityColors.critical,
  high: severityColors.high,
  medium: severityColors.medium,
  low: severityColors.low,
  unknown: severityColors.unknown,
};

export const severityChartGradients: Record<
  SeverityLevel,
  { from: string; to: string }
> = {
  critical: { from: "#ef4444", to: "#7f1d1d" },
  high: { from: "#f97316", to: "#7c2d12" },
  medium: { from: "#eab308", to: "#713f12" },
  low: { from: "#22c55e", to: "#14532d" },
  unknown: { from: "#94a3b8", to: "#1e293b" },
};

const theme = {
  colors,
  severityColors,
  severityOrder,
  statusColors,
  riskColors,
  spacing,
  radius,
  shadows,
  transitions,
  fontSizes,
  fonts,
  chartPalette,
  severityChartColors,
  severityChartGradients,
};

export default theme;
