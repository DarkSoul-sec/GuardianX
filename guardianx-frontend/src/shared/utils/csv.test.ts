import { describe, expect, it } from "vitest";

import { buildCsv } from "@/shared/utils/csv";

describe("csv utils", () => {
  const columns = [
    { header: "Name", value: (row: { name: string }) => row.name },
    {
      header: "Score",
      value: (row: { score: number | null }) => row.score,
    },
  ];

  it("writes a header row followed by data rows", () => {
    const csv = buildCsv(columns, [{ name: "Alpha", score: 10 }]);
    expect(csv).toBe("Name,Score\nAlpha,10");
  });

  it("escapes cells containing commas and quotes", () => {
    const csv = buildCsv(columns, [
      { name: 'He said "hi", ok', score: null },
    ]);
    expect(csv).toContain('"He said ""hi"", ok"');
  });

  it("renders null values as empty cells", () => {
    const csv = buildCsv(columns, [{ name: "Alpha", score: null }]);
    expect(csv).toBe("Name,Score\nAlpha,");
  });
});
