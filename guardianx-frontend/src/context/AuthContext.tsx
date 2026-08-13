import { useEffect, useState, type ReactNode } from "react";

import {
  getSetupStatus,
  login as loginService,
  logout as logoutService,
  saveTokens,
  isAuthenticated,
} from "@/services/auth";

import { AuthContext } from "./auth";

import type { LoginRequest } from "@/types/auth";

interface Props {
  children: ReactNode;
}

export function AuthProvider({ children }: Props) {
  const [authenticated, setAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [initialized, setInitialized] = useState(true);
  const [authMode, setAuthMode] = useState("local");

  useEffect(() => {
    let active = true;

    async function bootstrap() {
      setAuthenticated(isAuthenticated());

      try {
        const status = await getSetupStatus();
        if (active) {
          setInitialized(status.initialized);
          setAuthMode(status.auth_mode);
        }
      } catch {
        // Backend unreachable: assume initialized so an existing install is
        // never bounced into a setup request that would be rejected server-side.
        if (active) setInitialized(true);
      } finally {
        if (active) setLoading(false);
      }
    }

    bootstrap();
    return () => {
      active = false;
    };
  }, []);

  async function login(credentials: LoginRequest) {
    const response = await loginService(credentials);
    saveTokens(response);
    setAuthenticated(true);
  }

  async function logout() {
    await logoutService();
    setAuthenticated(false);
  }

  return (
    <AuthContext.Provider
      value={{
        authenticated,
        loading,
        initialized,
        authMode,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
