export interface FindingReport {
  cve: string | null;
  title: string;
  severity: string;
  cvss: number | null;
  status: string;
  description: string | null;
  recommendation: string | null;
  affected_service: string | null;
}

export interface ServiceReport {
  port: number;
  protocol: string | null;
  service: string | null;
  product: string | null;
  version: string | null;
  state: string | null;
  cpe: string | null;
}

export interface AssetReport {
  id: number;
  name: string;
  domain: string | null;
  ip_address: string | null;
  asset_type: string | null;
  risk_score: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
  total_findings: number;
  last_scan: string | null;
  scanner: string | null;
  services: ServiceReport[];
  findings: FindingReport[];
}

export interface ScanSummary {
  id: number;
  status: string;
  started_at: string | null;
  finished_at: string | null;
}

export interface ExecutiveSummary {
  assets: number;
  scans: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
  total_findings: number;
  risk_score: number;
}

export interface ExecutiveReport {
  generated_at: string;
  summary: ExecutiveSummary;
  top_assets: AssetReport[];
  recommendations: string[];
}

export interface TechnicalReport {
  generated_at: string;
  scan: ScanSummary;
  asset: AssetReport;
  findings: FindingReport[];
}
