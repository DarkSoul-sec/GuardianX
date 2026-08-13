import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import DevModeBanner from "@/components/DevModeBanner";

vi.mock("@/hooks/useSecurity", () => ({
  usePrivateNetworkScanningEnabled: vi.fn(),
}));

import { usePrivateNetworkScanningEnabled } from "@/hooks/useSecurity";

describe("DevModeBanner", () => {
  it("renders the warning banner when private scanning is enabled", () => {
    (usePrivateNetworkScanningEnabled as ReturnType<typeof vi.fn>).mockReturnValue(
      { data: { private_network_scanning_enabled: true } }
    );

    render(<DevModeBanner />);

    expect(screen.getByText("Development Mode")).toBeInTheDocument();
    expect(
      screen.getByText("Private Network Scanning Enabled")
    ).toBeInTheDocument();
  });

  it("renders nothing when private scanning is disabled", () => {
    (usePrivateNetworkScanningEnabled as ReturnType<typeof vi.fn>).mockReturnValue(
      { data: { private_network_scanning_enabled: false } }
    );

    const { container } = render(<DevModeBanner />);
    expect(container.firstChild).toBeNull();
  });

  it("renders nothing while the config is still loading", () => {
    (usePrivateNetworkScanningEnabled as ReturnType<typeof vi.fn>).mockReturnValue(
      { data: undefined }
    );

    const { container } = render(<DevModeBanner />);
    expect(container.firstChild).toBeNull();
  });
});
