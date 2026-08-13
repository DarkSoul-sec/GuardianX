export type VirusTotalResourceType = "url" | "domain" | "ip" | "file";

export type VirusTotalConnectionState =
  | "connected"
  | "invalid"
  | "rate_limited"
  | "unreachable"
  | "not_configured";

export interface VirusTotalVendorDetection {
  engine: string;
  category: string;
  result: string | null;
}

export interface VirusTotalLookupResponse {
  resource_type: VirusTotalResourceType;
  resource: string;
  permalink: string;
  found: boolean;
  detected: boolean;
  malicious: number;
  suspicious: number;
  undetected: number;
  harmless: number;
  timeout: number;
  total: number;
  detection_ratio: string;
  reputation: number;
  community_score: number;
  threat_category: string | null;
  last_analysis_date: string | null;
  vendor_detections: VirusTotalVendorDetection[];
}

export interface VirusTotalIntegrationStatus {
  provider: string;
  configured: boolean;
  status: VirusTotalConnectionState;
  message: string;
  last_tested_at: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface VirusTotalConnectResponse {
  status: VirusTotalIntegrationStatus;
}

export interface VirusTotalTestResponse {
  status: VirusTotalIntegrationStatus;
}

export interface VirusTotalDisconnectResponse {
  disconnected: boolean;
}
