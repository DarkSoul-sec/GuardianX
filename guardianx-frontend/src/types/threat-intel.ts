export type CveSeverity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "UNKNOWN";

export interface AttackTechnique {
  id: string;
  name: string;
  tactics: string[];
  description: string;
}

export interface VendorAdvisory {
  source: string;
  url: string;
  tags: string[];
}

export interface TrendingCve {
  id: string;
  title: string;
  description: string;
  severity: CveSeverity;
  cvss_score: number | null;
  published: string | null;
  last_modified: string | null;
  vendor: string | null;
  cwes: string[];
  epss_score: number | null;
  epss_percentile: number | null;
  exploited: boolean;
  kev_due_date: string | null;
  references: VendorAdvisory[];
}

export interface EpssHistoryPoint {
  date: string;
  score: number;
  percentile: number;
}

export interface CveDetail extends TrendingCve {
  attack_techniques: AttackTechnique[];
  advisories: VendorAdvisory[];
  epss_history: EpssHistoryPoint[];
}

export interface KevEntry {
  cve_id: string;
  vendor: string;
  product: string;
  vulnerability_name: string;
  description: string;
  required_action: string;
  due_date: string | null;
  date_added: string | null;
  known_ransomware_campaign: boolean;
}

export interface SeverityCount {
  severity: string;
  count: number;
}

export interface EpssBucket {
  bucket: string;
  count: number;
}

export interface RiskTimelinePoint {
  date: string;
  published_count: number;
  avg_epss: number;
}

export interface SourceStatus {
  source: string;
  configured: boolean;
  healthy: boolean;
}

export interface ThreatIntelStats {
  total_cves: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
  exploited_count: number;
  avg_epss: number;
  severity_distribution: SeverityCount[];
  epss_distribution: EpssBucket[];
  risk_timeline: RiskTimelinePoint[];
  sources: SourceStatus[];
}

export interface TrendingResponse {
  window_days: number;
  total: number;
  items: TrendingCve[];
}

export interface ThreatIntelSearchFilters {
  q: string;
  severity: string;
  year: string;
  vendor: string;
  exploited: boolean;
  sort: "published" | "epss" | "risk";
}

export interface ThreatIntelSearchResponse {
  query: string;
  severity: string | null;
  year: number | null;
  vendor: string | null;
  exploited_only: boolean;
  sort: "published" | "epss" | "risk";
  total: number;
  items: TrendingCve[];
}
