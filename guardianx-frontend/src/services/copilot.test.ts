import { describe, expect, it } from "vitest";

import { parseSseFrame } from "@/services/copilot";

describe("parseSseFrame", () => {
  it("parses a token event with JSON data", () => {
    const event = parseSseFrame(
      'event: token\ndata: {"type":"token","content":"Hello"}'
    );

    expect(event).toEqual({
      type: "token",
      content: "Hello",
    });
  });

  it("parses a done event including results", () => {
    const event = parseSseFrame(
      'event: done\ndata: {"type":"done","content":"done","results":[{"kind":"finding","title":"X"}]}'
    );

    expect(event).toEqual({
      type: "done",
      content: "done",
      results: [{ kind: "finding", title: "X" }],
    });
  });

  it("parses a meta event and keeps unknown fields", () => {
    const event = parseSseFrame(
      'event: meta\ndata: {"type":"meta","intent":"asset_risk","provider":"rules"}'
    );

    expect(event).toEqual({
      type: "meta",
      intent: "asset_risk",
      provider: "rules",
    });
  });

  it("returns null for empty data", () => {
    expect(parseSseFrame("event: token\ndata:")).toBeNull();
  });

  it("returns null for malformed JSON", () => {
    expect(parseSseFrame("event: token\ndata: not-json")).toBeNull();
  });
});
