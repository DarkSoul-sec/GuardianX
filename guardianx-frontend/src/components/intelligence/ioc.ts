import type { IntelligenceIocType } from "@/types/intelligence";

export interface IocMeta {
  label: string;
  placeholder: string;
  description: string;
}

export const IOC_META: Record<IntelligenceIocType, IocMeta> = {
  ip: {
    label: "IP Address",
    placeholder: "8.8.8.8",
    description: "IPv4 or IPv6 address reputation",
  },
  domain: {
    label: "Domain",
    placeholder: "example.com",
    description: "Hostname reputation and WHOIS",
  },
  url: {
    label: "URL",
    placeholder: "https://example.com",
    description: "URL scanning and reputation",
  },
  hash: {
    label: "SHA256 Hash",
    placeholder: "64-character SHA256 hash",
    description: "File-hash verdicts across AV engines",
  },
};

const SHA256_RE = /^[a-fA-F0-9]{64}$/;
const IPV4_RE = /^(\d{1,3}\.){3}\d{1,3}$/;
const HOSTNAME_RE =
  /^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})*$/;

function isIpv4(value: string): boolean {
  if (!IPV4_RE.test(value)) return false;
  return value.split(".").every((octet) => {
    const n = Number(octet);
    return n >= 0 && n <= 255 && String(n) === octet;
  });
}

function isIpv6(value: string): boolean {
  if (!value.includes(":")) return false;

  const segments = value.split("::");
  if (segments.length > 2) return false;

  const hexRe = /^[0-9a-fA-F]{1,4}$/;
  const groups = segments.flatMap((segment) => segment.split(":"));
  if (groups.some((group) => group !== "" && !hexRe.test(group))) {
    return false;
  }

  const nonEmpty = groups.filter((group) => group !== "").length;
  return segments.length === 2 ? nonEmpty < 8 : nonEmpty === 8;
}

/**
 * Auto-detect the indicator type of a raw search value, mirroring the backend
 * detection order: URL, SHA256 hash, IP address, then hostname.
 */
export function detectIocType(value: string): IntelligenceIocType | null {
  const raw = value.trim();
  if (!raw) return null;

  try {
    const parsed = new URL(raw);
    if (parsed.protocol === "http:" || parsed.protocol === "https:") {
      return "url";
    }
  } catch {
    // Not a URL.
  }

  if (SHA256_RE.test(raw)) return "hash";
  if (isIpv4(raw) || isIpv6(raw)) return "ip";
  if (HOSTNAME_RE.test(raw.toLowerCase())) return "domain";

  return null;
}
