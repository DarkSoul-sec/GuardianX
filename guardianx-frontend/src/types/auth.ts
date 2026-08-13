export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface AuthUser {
  username: string;
}

export interface AdminSetupRequest {
  username: string;
  password: string;
}

export interface SetupStatus {
  initialized: boolean;
  auth_mode: string;
}

export interface UserProfile {
  id: number;
  username: string;
  email: string | null;
  role: string;
  is_active: boolean;
  email_verified: boolean;
}

export interface UserUpdateRequest {
  username?: string;
  email?: string | null;
}

export interface PasswordChangeRequest {
  current_password: string;
  new_password: string;
}
