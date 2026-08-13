import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import VirusTotalIntelPanel from "@/components/virustotal/VirusTotalIntelPanel";
import type { VirusTotalLookupResponse } from "@/types/virustotal";

const found: VirusTotalLookupResponse = {
  resource_type: "ip",
  resource: "8.8.8.8",
  permalink: "https://www.virustotal.com/gui/ip-address/8.8.8.8",
  found: true,
  detected: true,
  malicious: 2,
  suspicious: 1,
  undetected: 10,
  harmless: 5,
  timeout: 0,
  total: 18,
  detection_ratio: "2/18",
  reputation: -3,
  community_score: 1,
  threat_category: "malware",
  last_analysis_date: "2026-08-01T00:00:00Z",
  vendor_detections: [
    { engine: "Avast", category: "malicious", result: "Win32:Malware-gen" },
    { engine: "Kaspersky", category: "malicious", result: "Trojan.Agent" },
    { engine: "Microsoft", category: "clean", result: null },
    { engine: "Sophos", category: "clean", result: null },
    { engine: "ESET", category: "clean", result: null },
    { engine: "CrowdStrike", category: "suspicious", result: "Suspicious" },
  ],
};

describe("VirusTotalIntelPanel", () => {
  it("renders a loading skeleton while loading", () => {
    const { container } = render(<VirusTotalIntelPanel loading />);
    expect(container.querySelector(".animate-shimmer")).not.toBeNull();
  });

  it("renders nothing when there is no data yet", () => {
    const { container } = render(<VirusTotalIntelPanel />);
    expect(container.firstChild).toBeNull();
  });

  it("renders a not-found note", () => {
    render(
      <VirusTotalIntelPanel
        query="1.2.3.4"
        data={{ ...found, found: false, resource: "1.2.3.4" }}
      />
    );
    expect(screen.getByText(/No VirusTotal analysis exists/i)).toBeInTheDocument();
  });

  it("shows summary stats and a threat category", () => {
    render(<VirusTotalIntelPanel data={found} />);

    expect(screen.getByText("2/18")).toBeInTheDocument();
    expect(screen.getByText("-3")).toBeInTheDocument();
    expect(screen.getByText("malware")).toBeInTheDocument();
    expect(screen.getByText("Avast")).toBeInTheDocument();
  });

  it("limits vendor rows and expands on demand", async () => {
    render(<VirusTotalIntelPanel data={found} />);

    expect(screen.getAllByText(/^clean$|^malicious$|^suspicious$/i).length).toBeGreaterThan(0);

    const toggle = screen.getByRole("button", { name: /Show all 6 vendors/i });
    expect(toggle).toBeInTheDocument();
  });
});
