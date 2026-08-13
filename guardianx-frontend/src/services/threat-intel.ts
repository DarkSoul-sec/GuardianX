import api from "./api";

import type {
  AttackTechnique,
  CveDetail,
  KevEntry,
  ThreatIntelSearchFilters,
  ThreatIntelSearchResponse,
  ThreatIntelStats,
  TrendingResponse,
} from "@/types/threat-intel";

class ThreatIntelService {
  async getStats(days: number): Promise<ThreatIntelStats> {
    const { data } = await api.get<ThreatIntelStats>("/threat-intel/stats", {
      params: { days },
    });
    return data;
  }

  async getTrending(days: number, limit: number): Promise<TrendingResponse> {
    const { data } = await api.get<TrendingResponse>("/threat-intel/trending", {
      params: { days, limit },
    });
    return data;
  }

  async search(
    filters: ThreatIntelSearchFilters
  ): Promise<ThreatIntelSearchResponse> {
    const { data } = await api.get<ThreatIntelSearchResponse>(
      "/threat-intel/search",
      {
        params: {
          q: filters.q || undefined,
          severity: filters.severity || undefined,
          year: filters.year || undefined,
          vendor: filters.vendor || undefined,
          exploited: filters.exploited || undefined,
          sort: filters.sort,
          limit: 20,
        },
      }
    );
    return data;
  }

  async getCve(cveId: string): Promise<CveDetail> {
    const { data } = await api.get<CveDetail>(
      `/threat-intel/cve/${encodeURIComponent(cveId)}`
    );
    return data;
  }

  async getKev(limit: number): Promise<KevEntry[]> {
    const { data } = await api.get<KevEntry[]>("/threat-intel/kev", {
      params: { limit },
    });
    return data;
  }

  async getAttackTechniques(tactic?: string): Promise<AttackTechnique[]> {
    const { data } = await api.get<AttackTechnique[]>(
      "/threat-intel/attack-techniques",
      {
        params: { tactic: tactic || undefined },
      }
    );
    return data;
  }
}

const threatIntelService = new ThreatIntelService();

export default threatIntelService;
