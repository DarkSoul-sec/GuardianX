import api from "./api";

import type {
  IntelligenceHistoryResponse,
  IntelligenceIocType,
  IntelligenceLookupResponse,
  IntelligenceStatus,
} from "@/types/intelligence";

export interface IntelligenceHistoryParams {
  iocType?: IntelligenceIocType;
  q?: string;
  page?: number;
  limit?: number;
}

class IntelligenceService {
  async lookup(value: string): Promise<IntelligenceLookupResponse> {
    const { data } = await api.post<IntelligenceLookupResponse>(
      "/intelligence/lookup",
      { value }
    );
    return data;
  }

  async getHistory(
    params: IntelligenceHistoryParams = {}
  ): Promise<IntelligenceHistoryResponse> {
    const { data } = await api.get<IntelligenceHistoryResponse>(
      "/intelligence/history",
      {
        params: {
          ioc_type: params.iocType || undefined,
          q: params.q || undefined,
          page: params.page ?? 1,
          limit: params.limit ?? 10,
        },
      }
    );
    return data;
  }

  async deleteHistory(id: number): Promise<void> {
    await api.delete(`/intelligence/history/${id}`);
  }

  async clearHistory(): Promise<void> {
    await api.delete("/intelligence/history");
  }

  async getStatus(): Promise<IntelligenceStatus> {
    const { data } = await api.get<IntelligenceStatus>("/intelligence/status");
    return data;
  }
}

const intelligenceService = new IntelligenceService();

export default intelligenceService;
