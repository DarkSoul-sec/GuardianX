import api from "./api";

import type { PhishingAnalysisResponse } from "@/types/phishing";

class PhishingService {
  async analyze(url: string): Promise<PhishingAnalysisResponse> {
    const { data } = await api.post<PhishingAnalysisResponse>("/phishing/analyze", {
      url,
    });
    return data;
  }
}

const phishingService = new PhishingService();

export default phishingService;
