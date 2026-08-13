export interface RecentScan {
  scan_id: number;
  asset_name: string;
  status: string;
  started_at: string | null;
  finished_at: string | null;
  finding_count: number;
}

export interface VulnerableAsset {
  asset_id: number;
  asset_name: string;
  risk_score: number;
  total_findings: number;
  critical_findings: number;
}

export interface RecentFinding {
  cve: string | null;
  title: string;
  severity: string;
  asset: string;
  created_at: string;
  status: string;
}

export interface RiskTrendPoint {
  date: string;
  score: number;
}

export interface AssetGrowthPoint {
  date: string;
  count: number;
}

export interface AssetDistributionItem {
  type: string;
  count: number;
}

export interface FindingsTrendPoint {
  date: string;
  critical: number;
  high: number;
  medium: number;
  low: number;
}

export interface TopVulnerability {
  cve: string | null;
  title: string;
  severity: string;
  cvss: number | null;
  status: string;
  asset: string;
}

export interface DashboardOverview {
  assets: number;
  completed_scans: number;
  open_ports: number;
  total_services: number;
  critical_findings: number;
  high_findings: number;
  medium_findings: number;
  low_findings: number;
  total_findings: number;
  risk_score: number;

  risk_trend: RiskTrendPoint[];
  asset_growth: AssetGrowthPoint[];
  asset_distribution: AssetDistributionItem[];
  findings_trend: FindingsTrendPoint[];
  top_vulnerabilities: TopVulnerability[];

  recent_scans: RecentScan[];

  top_vulnerable_assets: VulnerableAsset[];

  recent_findings: RecentFinding[];
}
