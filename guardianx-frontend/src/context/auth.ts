import { createContext, useContext } from "react";

import type { LoginRequest } from "@/types/auth";

export interface AuthContextType {
  authenticated: boolean;
  loading: boolean;
  initialized: boolean;
  authMode: string;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function useAuthContext() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuthContext must be used inside AuthProvider");
  }

  return context;
}
