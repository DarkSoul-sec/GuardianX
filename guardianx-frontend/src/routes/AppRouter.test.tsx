import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import AppRouter from "@/routes/AppRouter";
import { AuthProvider } from "@/context/AuthContext";
import { getSetupStatus, isAuthenticated } from "@/services/auth";

vi.mock("@/services/auth", () => ({
  getSetupStatus: vi.fn(),
  login: vi.fn(),
  logout: vi.fn(),
  saveTokens: vi.fn(),
  isAuthenticated: vi.fn(() => false),
}));

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <AuthProvider>
        <AppRouter />
      </AuthProvider>
    </MemoryRouter>
  );
}

function mockStatus(initialized: boolean) {
  vi.mocked(getSetupStatus).mockResolvedValue({
    initialized,
    auth_mode: "local",
  });
}

describe("AppRouter", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(isAuthenticated).mockReturnValue(false);
  });

  it("routes a fresh installation to the setup page", async () => {
    mockStatus(false);
    renderAt("/");

    expect(
      await screen.findByRole("button", { name: /Initialize GuardianX/i })
    ).toBeInTheDocument();
  });

  it("routes an initialized installation to login", async () => {
    mockStatus(true);
    renderAt("/");

    expect(
      await screen.findByRole("button", { name: "Login" })
    ).toBeInTheDocument();
  });

  it("no longer exposes the signup route", async () => {
    mockStatus(true);
    renderAt("/signup");

    expect(
      await screen.findByRole("button", { name: "Login" })
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /Sign Up/i })
    ).not.toBeInTheDocument();
  });

  it("no longer exposes the verify-email route", async () => {
    mockStatus(true);
    renderAt("/verify-email");

    expect(
      await screen.findByRole("button", { name: "Login" })
    ).toBeInTheDocument();
    expect(screen.queryByText("Email Verified")).not.toBeInTheDocument();
  });

  it("keeps the dashboard behind authentication", async () => {
    mockStatus(true);
    renderAt("/");

    expect(
      await screen.findByRole("button", { name: "Login" })
    ).toBeInTheDocument();
    expect(screen.queryByText(/Security Operations/i)).not.toBeInTheDocument();
  });
});
