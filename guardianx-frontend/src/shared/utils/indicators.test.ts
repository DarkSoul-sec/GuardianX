import { describe, expect, it } from "vitest";

import {
  extractDomains,
  extractIndicators,
  extractIps,
  extractSha256,
  extractUrls,
} from "./indicators";

describe("extractSha256", () => {
  it("returns lowercased 64-char hashes", () => {
    const hash = "A".repeat(64);
    expect(extractSha256(`Malware sample ${hash} dropped.`)).toEqual([
      hash.toLowerCase(),
    ]);
  });

  it("ignores shorter hex strings", () => {
    expect(extractSha256("abc123")).toEqual([]);
  });
});

describe("extractUrls", () => {
  it("finds http and https URLs", () => {
    expect(
      extractUrls("Visit https://evil.example.com/path and http://a.b/c")
    ).toEqual(["https://evil.example.com/path", "http://a.b/c"]);
  });

  it("strips trailing punctuation", () => {
    expect(extractUrls("See https://example.com/page?q=1.")).toEqual([
      "https://example.com/page?q=1",
    ]);
  });
});

describe("extractIps", () => {
  it("finds IPv4 addresses including with ports", () => {
    expect(extractIps("C2 at 192.168.1.5:443 reported.")).toEqual([
      "192.168.1.5",
    ]);
  });

  it("finds IPv6 addresses", () => {
    expect(extractIps("Server at 2001:db8::1")).toEqual(["2001:db8::1"]);
  });

  it("rejects octets over 255", () => {
    expect(extractIps("999.999.1.1")).toEqual([]);
  });
});

describe("extractDomains", () => {
  it("finds domains and drops the one inside a URL", () => {
    expect(
      extractDomains("Beacon https://evil.example.com and c2.example.net")
    ).toEqual(["c2.example.net"]);
  });

  it("drops an IP embedded in a domain-like string", () => {
    expect(extractDomains("192.168.1.5")).toEqual([]);
  });
});

describe("extractIndicators", () => {
  it("returns indicators ordered by specificity without duplicates", () => {
    const result = extractIndicators(
      `Hash ${"c".repeat(64)} beacon at https://evil.example.com, ip 10.0.0.1, host c2.example.net`
    );

    expect(result.map((item) => item.type)).toEqual([
      "file",
      "url",
      "ip",
      "domain",
    ]);
    expect(result[0].value).toBe("c".repeat(64));
    expect(result[1].value).toBe("https://evil.example.com");
    expect(result[2].value).toBe("10.0.0.1");
    expect(result[3].value).toBe("c2.example.net");
  });

  it("returns empty for unrelated text", () => {
    expect(extractIndicators("No indicators here.")).toEqual([]);
  });
});
