import { describe, expect, it } from "vitest";

import type { IntelligenceVendorDetection } from "@/types/intelligence";

import { filterDetections, sortDetections } from "./threatIndicators";

const detections: IntelligenceVendorDetection[] = [
  {
    engine: "VendorA",
    category: "malicious",
    result: "Trojan.Generic",
    engine_version: "1.2",
    update_date: "2024-05-01T00:00:00Z",
  },
  {
    engine: "VendorB",
    category: "suspicious",
    result: "suspicious",
    engine_version: "3.0",
    update_date: null,
  },
  {
    engine: "VendorC",
    category: "harmless",
    result: null,
    engine_version: null,
    update_date: "2024-01-01T00:00:00Z",
  },
];

describe("filterDetections", () => {
  it("returns all items for an empty query", () => {
    expect(filterDetections(detections, "")).toHaveLength(3);
    expect(filterDetections(detections, "   ")).toHaveLength(3);
  });

  it("filters by engine name", () => {
    const result = filterDetections(detections, "vendorb");
    expect(result).toHaveLength(1);
    expect(result[0].engine).toBe("VendorB");
  });

  it("filters by result text", () => {
    const result = filterDetections(detections, "trojan");
    expect(result).toHaveLength(1);
    expect(result[0].engine).toBe("VendorA");
  });

  it("filters by category", () => {
    const result = filterDetections(detections, "harmless");
    expect(result).toHaveLength(1);
    expect(result[0].engine).toBe("VendorC");
  });
});

describe("sortDetections", () => {
  it("sorts engines ascending and descending", () => {
    expect(sortDetections(detections, "engine", "asc").map((d) => d.engine)).toEqual([
      "VendorA",
      "VendorB",
      "VendorC",
    ]);
    expect(sortDetections(detections, "engine", "desc").map((d) => d.engine)).toEqual([
      "VendorC",
      "VendorB",
      "VendorA",
    ]);
  });

  it("sorts category with malicious first ascending", () => {
    const result = sortDetections(detections, "category", "asc");
    expect(result.map((d) => d.category)).toEqual([
      "malicious",
      "suspicious",
      "harmless",
    ]);
  });

  it("sorts category descending with malicious last", () => {
    const result = sortDetections(detections, "category", "desc");
    expect(result.map((d) => d.category)).toEqual([
      "harmless",
      "suspicious",
      "malicious",
    ]);
  });

  it("keeps null values last when sorting by version", () => {
    const result = sortDetections(detections, "engine_version", "asc");
    expect(result.map((d) => d.engine)).toEqual(["VendorA", "VendorB", "VendorC"]);
  });

  it("does not mutate the input array", () => {
    const original = [...detections];
    sortDetections(detections, "engine", "desc");
    expect(detections).toEqual(original);
  });
});
