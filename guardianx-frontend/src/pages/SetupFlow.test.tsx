import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import { AuthProvider } from "@/context/AuthContext";
import { useAuth } from "@/hooks/useAuth";
import Setup from "@/pages/Setup";
import Login from "@/pages/Login";
import { getSetupStatus, isAuthenticated, setupAdmin } from "@/services/auth";

vi.mock("@/services/auth", () => ({
  getSetupStatus: vi.fn(),
  setupAdmin: vi.fn(),
  login: vi.fn(),
  logout: vi.fn(),
  saveTokens: vi.fn(),
  isAuthenticated: vi.fn(() => false),
}));

// Surfaces the shared auth state so the tests can prove the context value
// flips to true after a successful setup (and stays false on failure).
function InitializedProbe() {
  const { initialized } = useAuth();
  return <span data-testid="initialized">{String(initialized)}</span>;
}

function mockStatus(initialized: boolean) {
  vi.mocked(getSetupStatus).mockResolvedValue({
    initialized,
    auth_mode: "local",
  });
}

function renderFlow(initialPath = "/setup") {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <AuthProvider>
        <InitializedProbe />
        <Routes>
          <Route path="/setup" element={<Setup />} />
          <Route path="/login" element={<Login />} />
        </Routes>
      </AuthProvider>
    </MemoryRouter>
  );
}

async function completeSetup(user: ReturnType<typeof userEvent.setup>) {
  await screen.findByRole("button", { name: /Initialize GuardianX/i });
  await user.type(screen.getByLabelText("Username"), "release-admin");
  await user.type(
    screen.getByLabelText("Password"),
    "Sup3rStrongPassword1!",
  );
  await user.type(
    screen.getByLabelText("Confirm Password"),
    "Sup3rStrongPassword1!",
  );
  await user.click(
    screen.getByRole("button", { name: /Initialize GuardianX/i }),
  );
}

describe("Fresh-install Setup -> Login transition", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(isAuthenticated).mockReturnValue(false);
    mockStatus(false);
  });

  it("renders Setup (not Login) on an uninitialized installation", async () => {
    renderFlow("/setup");

    expect(
      await screen.findByRole("button", { name: /Initialize GuardianX/i }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Login" }),
    ).not.toBeInTheDocument();
  });

  it("marks the installation initialized after a successful setup", async () => {
    vi.mocked(setupAdmin).mockResolvedValue({
      message: "GuardianX initialized successfully.",
    });
    const user = userEvent.setup();
    renderFlow("/setup");

    await completeSetup(user);

    expect(
      await screen.findByText("GuardianX Initialized"),
    ).toBeInTheDocument();
    expect(screen.getByTestId("initialized")).toHaveTextContent("true");
  });

  it("navigates to Login without a reload when Continue to Login is clicked", async () => {
    vi.mocked(setupAdmin).mockResolvedValue({
      message: "GuardianX initialized successfully.",
    });
    const user = userEvent.setup();
    renderFlow("/setup");

    await completeSetup(user);
    await screen.findByText("GuardianX Initialized");

    await user.click(
      screen.getByRole("link", { name: /Continue to Login/i }),
    );

    expect(
      await screen.findByRole("button", { name: "Login" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /Initialize GuardianX/i }),
    ).not.toBeInTheDocument();
    expect(screen.getByTestId("initialized")).toHaveTextContent("true");
  });

  it("does not redirect Login back to Setup after initialization", async () => {
    mockStatus(true);
    renderFlow("/login");

    expect(
      await screen.findByRole("button", { name: "Login" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /Initialize GuardianX/i }),
    ).not.toBeInTheDocument();
  });

  it("opens Login normally on an existing initialized installation", async () => {
    mockStatus(true);
    renderFlow("/login");

    expect(
      await screen.findByRole("button", { name: "Login" }),
    ).toBeInTheDocument();
  });

  it("redirects /setup to Login on an existing initialized installation", async () => {
    mockStatus(true);
    renderFlow("/setup");

    expect(
      await screen.findByRole("button", { name: "Login" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /Initialize GuardianX/i }),
    ).not.toBeInTheDocument();
  });

  it("leaves initialized=false and stays on Setup when setup fails", async () => {
    vi.mocked(setupAdmin).mockRejectedValue({
      response: {
        data: { detail: "GuardianX has already been initialized." },
      },
    });
    const user = userEvent.setup();
    renderFlow("/setup");

    await completeSetup(user);

    expect(
      await screen.findByText("GuardianX has already been initialized."),
    ).toBeInTheDocument();
    expect(screen.getByTestId("initialized")).toHaveTextContent("false");
    expect(
      screen.getByRole("button", { name: /Initialize GuardianX/i }),
    ).toBeInTheDocument();
  });
});
