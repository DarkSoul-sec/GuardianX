import { describe, expect, it } from "vitest";

import { detectIocType } from "./ioc";

describe("detectIocType", () => {
  it("detects http(s) URLs", () => {
    expect(detectIocType("https://example.com/path")).toBe("url");
    expect(detectIocType("http://8.8.8.8:8080/x")).toBe("url");
  });

  it("detects SHA256 hashes", () => {
    expect(detectIocType("a".repeat(64))).toBe("hash");
    expect(detectIocType("B".repeat(64))).toBe("hash");
  });

  it("detects IPv4 and IPv6 addresses", () => {
    expect(detectIocType("8.8.8.8")).toBe("ip");
    expect(detectIocType("2001:4860:4860::8888")).toBe("ip");
    expect(detectIocType("::1")).toBe("ip");
  });

  it("detects hostnames as domains", () => {
    expect(detectIocType("example.com")).toBe("domain");
    expect(detectIocType("sub.example.co.uk")).toBe("domain");
  });

  it("trims surrounding whitespace", () => {
    expect(detectIocType("  1.1.1.1  ")).toBe("ip");
  });

  it("returns null for empty or unrecognized values", () => {
    expect(detectIocType("")).toBeNull();
    expect(detectIocType("   ")).toBeNull();
    expect(detectIocType("not an ioc!!")).toBeNull();
    expect(detectIocType("ab cd")).toBeNull();
    expect(detectIocType("foo_bar")).toBeNull();
  });

  it("treats single-label hostnames and dotted numerics as domains", () => {
    expect(detectIocType("abc")).toBe("domain");
    expect(detectIocType("999.999.999.999")).toBe("domain");
  });
});
