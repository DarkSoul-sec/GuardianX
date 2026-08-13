import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import Login from "@/pages/Login";

const login = vi.fn();

const authState = {
  login,
  authenticated: false,
  loading: false,
  initialized: true,
  authMode: "local",
};

vi.mock("@/hooks/useAuth", () => ({
  useAuth: () => authState,
}));

function renderLogin() {
  return render(
    <MemoryRouter initialEntries={["/login"]}>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/setup" element={<div>SETUP PAGE</div>} />
      </Routes>
    </MemoryRouter>
  );
}

describe("Login", () => {
  beforeEach(() => {
    authState.authenticated = false;
    authState.loading = false;
    authState.initialized = true;
    authState.authMode = "local";
    login.mockReset();
  });

  it("renders the login form without a public signup link", () => {
    renderLogin();

    expect(screen.getByLabelText("Username")).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Login" })).toBeInTheDocument();
    expect(
      screen.queryByRole("link", { name: /Create account/i })
    ).not.toBeInTheDocument();
  });

  it("redirects to the setup page on a fresh installation", () => {
    authState.initialized = false;
    renderLogin();

    expect(screen.getByText("SETUP PAGE")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Login" })).not.toBeInTheDocument();
  });

  it("submits the credentials to the auth context", async () => {
    const user = userEvent.setup();
    login.mockResolvedValue(undefined);
    renderLogin();

    await user.type(screen.getByLabelText("Username"), "admin");
    await user.type(screen.getByLabelText("Password"), "Sup3rStrongPassword1!");
    await user.click(screen.getByRole("button", { name: "Login" }));

    expect(login).toHaveBeenCalledWith({
      username: "admin",
      password: "Sup3rStrongPassword1!",
    });
  });

  it("shows an error on invalid credentials", async () => {
    const user = userEvent.setup();
    login.mockRejectedValue(new Error("bad credentials"));
    renderLogin();

    await user.type(screen.getByLabelText("Username"), "admin");
    await user.type(screen.getByLabelText("Password"), "WrongPassword123!");
    await user.click(screen.getByRole("button", { name: "Login" }));

    expect(
      await screen.findByText("Invalid username or password.")
    ).toBeInTheDocument();
  });
});
