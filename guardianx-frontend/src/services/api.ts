import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";

import { API_BASE_URL, STORAGE_KEYS } from "@/shared/constants";

interface RetriableConfig extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

export function clearSession() {
  localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
  localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
}

export function redirectToLogin() {
  clearSession();
  if (!window.location.pathname.startsWith("/login")) {
    window.location.assign("/login");
  }
}

let refreshPromise: Promise<boolean> | null = null;

async function tryRefresh(): Promise<boolean> {
  const refreshToken = localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
  if (!refreshToken) return false;

  try {
    const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
      refresh_token: refreshToken,
    });
    const data = response.data as { access_token?: string; refresh_token?: string };

    if (data.access_token) {
      localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, data.access_token);
    }
    if (data.refresh_token) {
      localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, data.refresh_token);
    }
    return !!data.access_token;
  } catch {
    return false;
  }
}

function singleFlightRefresh(): Promise<boolean> {
  if (!refreshPromise) {
    refreshPromise = tryRefresh().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<unknown>) => {
    const original = error.config as RetriableConfig | undefined;
    const status = error.response?.status;
    const url = original?.url ?? "";

    const isAuthRoute = url.includes("/auth/login") || url.includes("/auth/refresh");
    const onLoginPage = window.location.pathname.startsWith("/login");

    if (status === 401 && original && !original._retry && !isAuthRoute && !onLoginPage) {
      original._retry = true;
      const refreshed = await singleFlightRefresh();

      if (refreshed) {
        return api(original);
      }
    }

    if (status === 401) {
      redirectToLogin();
    }

    return Promise.reject(error);
  }
);

export default api;
