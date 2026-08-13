import api from "./api";

import type {
  VirusTotalConnectResponse,
  VirusTotalDisconnectResponse,
  VirusTotalIntegrationStatus,
  VirusTotalLookupResponse,
  VirusTotalResourceType,
  VirusTotalTestResponse,
} from "@/types/virustotal";

class VirusTotalService {
  async lookupUrl(url: string): Promise<VirusTotalLookupResponse> {
    const { data } = await api.post<VirusTotalLookupResponse>(
      "/intelligence/url",
      { value: url }
    );
    return data;
  }

  async lookupDomain(domain: string): Promise<VirusTotalLookupResponse> {
    const { data } = await api.post<VirusTotalLookupResponse>(
      "/intelligence/domain",
      { value: domain }
    );
    return data;
  }

  async lookupIp(ip: string): Promise<VirusTotalLookupResponse> {
    const { data } = await api.post<VirusTotalLookupResponse>(
      "/intelligence/ip",
      { value: ip }
    );
    return data;
  }

  async lookupFileHash(hash: string): Promise<VirusTotalLookupResponse> {
    const { data } = await api.post<VirusTotalLookupResponse>(
      "/intelligence/hash",
      { value: hash }
    );
    return data;
  }

  async lookup(
    type: VirusTotalResourceType,
    value: string
  ): Promise<VirusTotalLookupResponse> {
    switch (type) {
      case "url":
        return this.lookupUrl(value);
      case "domain":
        return this.lookupDomain(value);
      case "ip":
        return this.lookupIp(value);
      case "file":
        return this.lookupFileHash(value);
    }
  }

  async getStatus(): Promise<VirusTotalIntegrationStatus> {
    const { data } = await api.get<VirusTotalIntegrationStatus>(
      "/integrations/virustotal/status"
    );
    return data;
  }

  async connect(apiKey: string): Promise<VirusTotalConnectResponse> {
    const { data } = await api.post<VirusTotalConnectResponse>(
      "/integrations/virustotal/connect",
      { api_key: apiKey }
    );
    return data;
  }

  async testConnection(apiKey?: string): Promise<VirusTotalTestResponse> {
    const { data } = await api.post<VirusTotalTestResponse>(
      "/integrations/virustotal/test",
      { api_key: apiKey }
    );
    return data;
  }

  async disconnect(): Promise<VirusTotalDisconnectResponse> {
    const { data } = await api.delete<VirusTotalDisconnectResponse>(
      "/integrations/virustotal/disconnect"
    );
    return data;
  }
}

const virusTotalService = new VirusTotalService();

export default virusTotalService;
