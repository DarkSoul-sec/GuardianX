/**
 * Threat-indicator extraction helpers used to surface "Analyze with
 * VirusTotal" actions from free-form finding text.
 */

import type { VirusTotalResourceType } from "@/types/virustotal";

export interface ExtractedIndicator {
  type: VirusTotalResourceType;
  value: string;
}

const SHA256_PATTERN = /\b[0-9a-fA-F]{64}\b/g;

const URL_PATTERN = /\bhttps?:\/\/[^\s<>"'()]+/gi;

const IP_PATTERN =
  /\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b|\b[0-9a-fA-F]{1,4}(?::[0-9a-fA-F]{0,4}){2,7}\b/g;

const DOMAIN_PATTERN =
  /\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}\b/gi;

const TRAILING_PUNCTUATION = /[.,;:!?)\]}]+$/g;

export function extractSha256(text: string): string[] {
  return unique(text.match(SHA256_PATTERN) ?? []).map((value) =>
    value.toLowerCase()
  );
}

export function extractUrls(text: string): string[] {
  return unique((text.match(URL_PATTERN) ?? []).map(cleanUrl)).filter(Boolean);
}

export function extractIps(text: string): string[] {
  return unique(text.match(IP_PATTERN) ?? []);
}

export function extractDomains(text: string): string[] {
  const domains = unique(text.match(DOMAIN_PATTERN) ?? []);
  const urls = extractUrls(text);
  const ips = extractIps(text);

  return domains.filter((domain) => {
    if (urls.some((url) => url.includes(domain))) return false;
    if (ips.some((ip) => domain.includes(ip))) return false;
    return true;
  });
}

/**
 * Collect distinct indicators from free-form text, ordered by specificity
 * (SHA256, URL, IP, domain). Domains embedded in a URL/IP are not repeated.
 */
export function extractIndicators(text: string): ExtractedIndicator[] {
  const indicators: ExtractedIndicator[] = [];

  for (const value of extractSha256(text)) {
    indicators.push({ type: "file", value });
  }
  for (const value of extractUrls(text)) {
    indicators.push({ type: "url", value });
  }
  for (const value of extractIps(text)) {
    indicators.push({ type: "ip", value });
  }
  for (const value of extractDomains(text)) {
    indicators.push({ type: "domain", value });
  }

  return indicators;
}

function cleanUrl(value: string): string {
  return value.replace(TRAILING_PUNCTUATION, "");
}

function unique(values: string[]): string[] {
  return Array.from(new Set(values.map((value) => value.toLowerCase())));
}
