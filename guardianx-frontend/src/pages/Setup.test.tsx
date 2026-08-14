import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";

import Setup from "@/pages/Setup";
import { setupAdmin } from "@/services/auth";

vi.mock("@/services/auth", () => ({
  setupAdmin: vi.fn(),
}));

vi.mock("@/hooks/useAuth", () => ({
  useAuth: () => ({
    authenticated: false,
    loading: false,
    initialized: false,
    authMode: "local",
    markInitialized: vi.fn(),
  }),
}));

function renderSetup() {
  return render(
    <MemoryRouter>
      <Setup />
    </MemoryRouter>
  );
}

async function fillForm() {
  const user = userEvent.setup();
  await user.type(screen.getByLabelText("Username"), "admin");
  await user.type(
    screen.getByLabelText("Password"),
    "Sup3rStrongPassword1!"
  );
  await user.type(
    screen.getByLabelText("Confirm Password"),
    "Sup3rStrongPassword1!"
  );
  await user.click(
    screen.getByRole("button", { name: /Initialize GuardianX/i })
  );
}

describe("Setup", () => {
  it("renders the first-run administrator form without email verification", () => {
    renderSetup();

    expect(
      screen.getByText(/Welcome to your local GuardianX installation/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Create the administrator account to secure this instance/i)
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Username")).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toBeInTheDocument();
    expect(screen.getByLabelText("Confirm Password")).toBeInTheDocument();
    expect(screen.queryByLabelText(/email/i)).not.toBeInTheDocument();
  });

  it("rejects a password mismatch", async () => {
    const user = userEvent.setup();
    renderSetup();

    await user.type(screen.getByLabelText("Username"), "admin");
    await user.type(
      screen.getByLabelText("Password"),
      "Sup3rStrongPassword1!"
    );
    await user.type(screen.getByLabelText("Confirm Password"), "different");
    await user.click(
      screen.getByRole("button", { name: /Initialize GuardianX/i })
    );

    expect(await screen.findByText("Passwords do not match.")).toBeInTheDocument();
    expect(setupAdmin).not.toHaveBeenCalled();
  });

  it("initializes the instance and offers a path to login on success", async () => {
    vi.mocked(setupAdmin).mockResolvedValue({
      message: "GuardianX initialized successfully.",
    });

    renderSetup();
    await fillForm();

    expect(setupAdmin).toHaveBeenCalledWith({
      username: "admin",
      password: "Sup3rStrongPassword1!",
    });

    expect(
      await screen.findByText("GuardianX Initialized")
    ).toBeInTheDocument();
    const continueLink = screen.getByRole("link", {
      name: /Continue to Login/i,
    });
    expect(continueLink).toHaveAttribute("href", "/login");
  });

  it("shows the backend error message on failure", async () => {
    vi.mocked(setupAdmin).mockRejectedValue({
      response: {
        data: { detail: "GuardianX has already been initialized." },
      },
    });

    renderSetup();
    await fillForm();

    expect(
      await screen.findByText("GuardianX has already been initialized.")
    ).toBeInTheDocument();
  });
});
