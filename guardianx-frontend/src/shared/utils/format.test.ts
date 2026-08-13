import { describe, expect, it } from "vitest";

import {
  formatDate,
  formatDuration,
  formatNumber,
  formatRelativeTime,
  toTitleCase,
  truncate,
} from "@/shared/utils/format";

describe("format utils", () => {
  it("returns a dash for missing dates", () => {
    expect(formatDate(null)).toBe("-");
    expect(formatDate("not-a-date")).toBe("-");
  });

  it("formats a valid date into a readable string", () => {
    const result = formatDate("2026-08-05T10:00:00Z");
    expect(result).not.toBe("-");
    expect(result).toContain("2026");
  });

  it("truncates long strings with an ellipsis", () => {
    expect(truncate("abcdefghij", 5)).toBe("abcde…");
  });

  it("returns the original string when shorter than the limit", () => {
    expect(truncate("abc", 5)).toBe("abc");
  });

  it("converts snake_case to title case", () => {
    expect(toTitleCase("in_progress")).toBe("In Progress");
  });

  it("formats numbers with thousands separators", () => {
    expect(formatNumber(1234567)).toBe("1,234,567");
  });

  it("formats durations in human terms", () => {
    expect(
      formatDuration("2026-08-05T10:00:00Z", "2026-08-05T10:01:30Z")
    ).toBe("1m 30s");
    expect(
      formatDuration("2026-08-05T10:00:00Z", "2026-08-05T11:00:00Z")
    ).toBe("1h 0m");
    expect(formatDuration(null, null)).toBe("-");
  });

  it("formats relative times", () => {
    expect(formatRelativeTime(null)).toBe("-");
  });
});
