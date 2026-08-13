import api from "./api";
import type {
  AdminSetupRequest,
  LoginRequest,
  LoginResponse,
  PasswordChangeRequest,
  SetupStatus,
  UserProfile,
  UserUpdateRequest,
} from "@/types/auth";
import { STORAGE_KEYS } from "@/shared/constants";

export async function login(credentials: LoginRequest): Promise<LoginResponse> {
  const formData = new URLSearchParams();
  formData.append("grant_type", "password");
  formData.append("username", credentials.username);
  formData.append("password", credentials.password);
  formData.append("scope", "");

  const response = await api.post<LoginResponse>("/auth/login", formData, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
  });

  return response.data;
}

export async function logout() {
  const refreshToken = localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);

  try {
    if (refreshToken) {
      await api.post("/auth/logout", { refresh_token: refreshToken });
    }
  } catch {
    // Session is cleared regardless of whether the server revoke succeeds.
  } finally {
    localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
  }
}

export function saveTokens(data: LoginResponse) {
  localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, data.access_token);
  localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, data.refresh_token);
}

export function getAccessToken() {
  return localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
}

export function isAuthenticated() {
  return !!getAccessToken();
}

export async function getSetupStatus(): Promise<SetupStatus> {
  const response = await api.get<SetupStatus>("/auth/setup-status");
  return response.data;
}

export async function setupAdmin(data: AdminSetupRequest): Promise<{ message: string }> {
  const response = await api.post<{ message: string }>("/auth/setup", data);
  return response.data;
}

export async function forgotPassword(email: string) {
  const response = await api.post("/auth/forgot-password", { email });
  return response.data;
}

export async function resetPassword(token: string, newPassword: string) {
  const response = await api.post("/auth/reset-password", {
    token,
    new_password: newPassword,
  });
  return response.data;
}

export async function getProfile(): Promise<UserProfile> {
  const response = await api.get<UserProfile>("/users/me");
  return response.data;
}

export async function updateProfile(data: UserUpdateRequest): Promise<UserProfile> {
  const response = await api.patch<UserProfile>("/users/me", data);
  return response.data;
}

export async function changePassword(data: PasswordChangeRequest): Promise<UserProfile> {
  const response = await api.post<UserProfile>("/users/me/password", data);
  return response.data;
}
