export type UserRole =
  | "ADMIN"
  | "SECURITY_ENGINEER"
  | "ANALYST"
  | "VIEWER"
  | "USER";

export interface User {
  id: number;
  username: string;
  email: string | null;
  role: UserRole;
  is_active: boolean;
  email_verified: boolean;
}

export interface ActiveSession {
  id: number;
  created_at: string;
  expires_at: string;
  user_agent: string | null;
  ip_address: string | null;
}

export interface UpdateProfileDto {
  username?: string;
  email?: string | null;
}

export interface ChangePasswordDto {
  current_password: string;
  new_password: string;
}
