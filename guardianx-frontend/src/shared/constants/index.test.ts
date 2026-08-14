import { describe, expect, it } from "vitest";

import { resolveApiBaseUrl } from "@/shared/constants";

describe("resolveApiBaseUrl (fresh-install auth routing guard)", () => {
  it("uses a non-empty configured value as-is", () => {
    expect(resolveApiBaseUrl("http://localhost:8080/api")).toBe(
      "http://localhost:8080/api",
    );
    expect(resolveApiBaseUrl("/api")).toBe("/api");
  });

  it("falls back to a relative /api when VITE_API_URL is unset", () => {
    expect(resolveApiBaseUrl(undefined)).toBe("/api");
  });

  it("falls back to a relative /api when VITE_API_URL is an empty string", () => {
    // This is the root cause: an empty string must NOT be kept (the previous
    // `??` operator kept ""), because an empty base drops the /api prefix and
    // makes /auth/setup-status 404, hiding first-run setup.
    expect(resolveApiBaseUrl("")).toBe("/api");
  });

  it("falls back to a relative /api when VITE_API_URL is only whitespace", () => {
    expect(resolveApiBaseUrl("   ")).toBe("/api");
  });

  it("never yields an empty base URL", () => {
    expect(resolveApiBaseUrl(undefined).length).toBeGreaterThan(0);
    expect(resolveApiBaseUrl("").length).toBeGreaterThan(0);
  });

  it("never yields the absolute dev localhost as the production default", () => {
    // An absolute http://127.0.0.1:8000/api would route from the browser to a
    // port that is never published to the host.
    expect(resolveApiBaseUrl(undefined)).not.toMatch(/127\.0\.0\.1:8000/);
    expect(resolveApiBaseUrl("")).not.toMatch(/127\.0\.0\.1:8000/);
  });
});
