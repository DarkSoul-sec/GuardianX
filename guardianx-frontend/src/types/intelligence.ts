export type IntelligenceIocType = "ip" | "domain" | "url" | "hash";

export type IntelligenceThreatLevel =
  | "critical"
  | "high"
  | "medium"
  | "low"
  | "clean"
  | "unknown";

export interface IntelligenceVendorDetection {
  engine: string;
  category: string;
  result: string | null;
  engine_version: string | null;
  update_date: string | null;
}

export interface IntelligenceCommunityVotes {
  malicious: number;
  harmless: number;
}

export interface IntelligenceMitreMapping {
  tactic: string;
  technique_id: string;
  technique: string;
  description: string | null;
}

export interface IntelligenceReport {
  resource_type: IntelligenceIocType;
  resource: string;
  permalink: string;
  found: boolean;
  detected: boolean;
  threat_level: IntelligenceThreatLevel;
  risk_score: number;
  reputation: number;
  community_score: number;
  detection_ratio: string;
  threat_category: string | null;
  last_analysis: string | null;
  country: string | null;
  asn: string | null;
  as_owner: string | null;
  registrar: string | null;
  creation_date: string | null;
  first_seen: string | null;
  first_submission: string | null;
  last_submission: string | null;
  submission_count: number;
  community_votes: IntelligenceCommunityVotes;
  malicious: number;
  suspicious: number;
  harmless: number;
  undetected: number;
  total: number;
  categories: string[];
  tags: string[];
  mitre: IntelligenceMitreMapping[];
  vendor_detections: IntelligenceVendorDetection[];
  from_cache: boolean;
}

export interface IntelligenceLookupResponse {
  report: IntelligenceReport;
  history_id: number | null;
}

export interface IntelligenceHistoryItem {
  id: number;
  resource_type: IntelligenceIocType;
  resource: string;
  threat_level: IntelligenceThreatLevel;
  risk_score: number;
  reputation: number;
  detected: boolean;
  malicious: number;
  suspicious: number;
  harmless: number;
  undetected: number;
  detection_ratio: string;
  threat_category: string | null;
  created_at: string;
}

export interface IntelligenceHistoryResponse {
  items: IntelligenceHistoryItem[];
  total: number;
  page: number;
  limit: number;
}

export interface IntelligenceStatus {
  provider: string;
  configured: boolean;
}
