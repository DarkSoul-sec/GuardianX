import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import VirusTotalSettingsCard from "@/components/virustotal/VirusTotalSettingsCard";

vi.mock("@/hooks/useVirusTotal", () => ({
  useVirusTotalStatus: vi.fn(),
  useVirusTotalConnect: vi.fn(),
  useVirusTotalTest: vi.fn(),
  useVirusTotalDisconnect: vi.fn(),
}));

vi.mock("@/hooks/useToastContext", () => ({
  useToastContext: () => ({
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
  }),
}));

import {
  useVirusTotalConnect,
  useVirusTotalDisconnect,
  useVirusTotalStatus,
  useVirusTotalTest,
} from "@/hooks/useVirusTotal";

function mockMutations() {
  (useVirusTotalConnect as ReturnType<typeof vi.fn>).mockReturnValue({
    isPending: false,
    mutate: vi.fn(),
  });
  (useVirusTotalTest as ReturnType<typeof vi.fn>).mockReturnValue({
    isPending: false,
    mutate: vi.fn(),
  });
  (useVirusTotalDisconnect as ReturnType<typeof vi.fn>).mockReturnValue({
    isPending: false,
    mutate: vi.fn(),
  });
}

describe("VirusTotalSettingsCard", () => {
  it("renders the not-configured state", () => {
    (useVirusTotalStatus as ReturnType<typeof vi.fn>).mockReturnValue({
      data: {
        configured: false,
        status: "not_configured",
        message: "Add your VirusTotal API key to get started.",
        last_tested_at: null,
      },
      isLoading: false,
    });
    mockMutations();

    render(<VirusTotalSettingsCard />);

    expect(screen.getByText("VirusTotal")).toBeInTheDocument();
    expect(screen.getByText("Not Configured")).toBeInTheDocument();
    expect(screen.getByText(/Add your VirusTotal API key/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Save Key/i })).toBeDisabled();
  });

  it("enables Save Key once a valid-length key is entered", () => {
    (useVirusTotalStatus as ReturnType<typeof vi.fn>).mockReturnValue({
      data: {
        configured: false,
        status: "not_configured",
        message: "Add your VirusTotal API key to get started.",
        last_tested_at: null,
      },
      isLoading: false,
    });
    mockMutations();

    render(<VirusTotalSettingsCard />);

    const input = screen.getByLabelText("API Key");
    fireEvent.change(input, { target: { value: "a".repeat(64) } });

    expect(screen.getByRole("button", { name: /Save Key/i })).toBeEnabled();
  });

  it("shows a masked key and Remove button when configured", () => {
    (useVirusTotalStatus as ReturnType<typeof vi.fn>).mockReturnValue({
      data: {
        configured: true,
        status: "connected",
        message: "Connected — API key is valid.",
        last_tested_at: "2026-08-06T12:00:00Z",
      },
      isLoading: false,
    });
    mockMutations();

    render(<VirusTotalSettingsCard />);

    expect(screen.getByText("Connected")).toBeInTheDocument();
    expect(screen.getByText(/••••••/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Remove Key/i })).toBeEnabled();
  });
});
