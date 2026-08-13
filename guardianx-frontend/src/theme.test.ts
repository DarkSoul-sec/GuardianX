import { describe, expect, it } from "vitest";

import {
  exposureLevel,
  riskLevel,
  severityChartColors,
  type SeverityLevel,
} from "@/theme";

describe("theme helpers", () => {
  it("classifies risk scores into levels", () => {
    expect(riskLevel(80)).toBe("critical");
    expect(riskLevel(60)).toBe("high");
    expect(riskLevel(40)).toBe("medium");
    expect(riskLevel(10)).toBe("low");
  });

  it("classifies exposure from the attack-surface score", () => {
    expect(exposureLevel(80, false)).toBe("critical");
    expect(exposureLevel(60, false)).toBe("high");
    expect(exposureLevel(40, false)).toBe("medium");
    expect(exposureLevel(10, false)).toBe("low");
  });

  it("raises exposure one step for internet-facing assets", () => {
    expect(exposureLevel(60, true)).toBe("critical");
    expect(exposureLevel(40, true)).toBe("high");
    expect(exposureLevel(10, true)).toBe("medium");
    expect(exposureLevel(80, true)).toBe("critical");
  });

  it("provides a color for every severity level", () => {
    const levels: SeverityLevel[] = ["critical", "high", "medium", "low", "unknown"];
    for (const level of levels) {
      expect(severityChartColors[level]).toMatch(/^#[0-9a-f]{6}$/i);
    }
  });
});
