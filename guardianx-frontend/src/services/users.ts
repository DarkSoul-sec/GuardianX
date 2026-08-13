import api from "./api";
import type {
  ActiveSession,
  ChangePasswordDto,
  UpdateProfileDto,
  User,
} from "@/types/user";

class UserService {
  async getMe(): Promise<User> {
    const { data } = await api.get<User>("/users/me");
    return data;
  }

  async updateProfile(dto: UpdateProfileDto): Promise<User> {
    const { data } = await api.patch<User>("/users/me", dto);
    return data;
  }

  async changePassword(dto: ChangePasswordDto): Promise<User> {
    const { data } = await api.post<User>("/users/me/password", dto);
    return data;
  }

  async listSessions(): Promise<ActiveSession[]> {
    const { data } = await api.get<{ sessions: ActiveSession[] }>(
      "/users/me/sessions"
    );
    return data.sessions;
  }

  async revokeSession(sessionId: number): Promise<void> {
    await api.delete(`/users/me/sessions/${sessionId}`);
  }

  async revokeAllSessions(): Promise<void> {
    await api.post("/users/me/sessions/revoke-all");
  }
}

const userService = new UserService();

export default userService;
