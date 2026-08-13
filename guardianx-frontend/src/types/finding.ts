export type FindingSeverity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "UNKNOWN";

export type FindingStatus =
  | "OPEN"
  | "IN_PROGRESS"
  | "RESOLVED"
  | "FALSE_POSITIVE"
  | "ACCEPTED_RISK";

export interface Finding {
  id: number;
  title: string;
  severity: FindingSeverity;
  cve: string | null;
  cvss: number | null;
  status: FindingStatus;
  assigned_to: number | null;
  assigned_to_name: string | null;
  due_date: string | null;
  created_at: string;
  updated_at: string;
  asset_name: string | null;
  affected_service: string | null;
}

export interface FindingDetail {
  id: number;
  title: string;
  description: string | null;
  severity: FindingSeverity;
  cve: string | null;
  cvss: number | null;
  affected_asset: string | null;
  affected_service: string | null;
  recommendation: string | null;
  status: FindingStatus;
  assigned_to: number | null;
  assigned_to_name: string | null;
  notes: string | null;
  due_date: string | null;
  created_at: string;
  updated_at: string;
  provider: string | null;
  lookup_method: string | null;
  confidence: string | null;
}

export interface VulnerabilityIntelligence {
  id: string;
  cvss_score: number | null;
  published: string | null;
  last_modified: string | null;
  cwes: string[];
  affected_vendors: string[];
  affected_products: string[];
  epss_score: number | null;
  epss_percentile: number | null;
  exploited: boolean;
  exploit_status: string;
  guardianx_risk_score: number;
  threat_level: string;
  ai_summary: string;
  references: Array<{ url: string; source: string; tags: string[] }>;
  attack_techniques: Array<{ id: string; name: string; tactics: string[]; description: string }>;
}

export interface FindingIntelligenceResponse {
  status: "not_available" | "pending" | "ready" | "unavailable";
  intelligence: VulnerabilityIntelligence | null;
}

export interface FindingActivity {
  id: number;
  finding_id: number;
  user_id: number | null;
  username: string | null;
  action: string;
  old_value: string | null;
  new_value: string | null;
  created_at: string;
}

export interface FindingStats {
  total: number;
  open: number;
  in_progress: number;
  resolved: number;
  false_positive: number;
  accepted_risk: number;
  by_severity: Record<string, number>;
}

export interface Assignee {
  id: number;
  username: string;
}

export interface FindingTriageUpdate {
  status?: FindingStatus;
  assignee_id?: number | null;
  notes?: string | null;
  due_date?: string | null;
}

export interface BulkStatusUpdate {
  ids: number[];
  status: FindingStatus;
}

export interface BulkUpdateResult {
  updated: number;
  ids: number[];
}

export interface FindingListResponse {
  items: Finding[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface FindingQueryParams {
  page?: number;
  size?: number;
  severity?: FindingSeverity;
  status?: FindingStatus;
  asset?: string;
  cve?: string;
  search?: string;
  assigned?: "me" | "unassigned";
  sort_by?: string;
  sort_order?: "asc" | "desc";
}
