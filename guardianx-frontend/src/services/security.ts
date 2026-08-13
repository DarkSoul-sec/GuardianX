import api from "./api";

import type { SecurityConfig } from "@/types/security";

class SecurityService {
  async getConfig(): Promise<SecurityConfig> {
    const { data } = await api.get<SecurityConfig>("/security/config");
    return data;
  }
}

const securityService = new SecurityService();

export default securityService;