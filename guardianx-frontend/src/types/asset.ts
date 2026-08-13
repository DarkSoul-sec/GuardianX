export type AssetType =
  | "SERVER"
  | "WORKSTATION"
  | "WEBSITE"
  | "DOMAIN"
  | "IP_ADDRESS"
  | "API"
  | "CLOUD"
  | "MOBILE"
  | "OTHER";

export type Criticality =
  | "LOW"
  | "MEDIUM"
  | "HIGH"
  | "CRITICAL";

export interface Asset {
  id: number;
  name: string;
  asset_type: AssetType;

  ip_address: string | null;
  domain: string | null;
  operating_system: string | null;
  environment: string | null;
  owner: string | null;
  criticality: Criticality | null;
  description: string | null;

  created_by: number;
  created_at: string;
  updated_at: string;
}

export interface CreateAssetDto {
  name: string;
  asset_type: AssetType;

  ip_address?: string;
  domain?: string;
  operating_system?: string;
  environment?: string;
  owner?: string;
  criticality?: Criticality;
  description?: string;
}

export interface UpdateAssetDto {
  name?: string;
  asset_type?: AssetType;

  ip_address?: string;
  domain?: string;
  operating_system?: string;
  environment?: string;
  owner?: string;
  criticality?: Criticality;
  description?: string;
}

export interface AssetServiceItem {
  port: number;
  protocol: string;
  product: string | null;
  version: string | null;
  cpe: string | null;
  state: string;
}

export interface AssetRecentScan {
  scan_id: number;
  status: string;
  started_at: string | null;
  finished_at: string | null;
  total_findings: number;
}

export interface AssetRecentFinding {
  cve: string | null;
  severity: string;
  title: string;
  status: string;
  recommendation: string | null;
  cvss: number | null;
}

export interface AssetDetails {
  id: number;
  name: string;
  hostname: string | null;
  ip_address: string | null;
  asset_type: AssetType;
  domain: string | null;
  operating_system: string | null;
  environment: string | null;
  owner: string | null;
  criticality: Criticality | null;
  description: string | null;

  created_at: string;
  updated_at: string;

  risk_score: number;
  security_score: number;
  total_findings: number;
  critical: number;
  high: number;
  medium: number;
  low: number;

  attack_surface_score: number;
  internet_facing: boolean;
  open_ports: number[];
  technologies: string[];
  ai_summary: string;

  services: AssetServiceItem[];
  recent_scans: AssetRecentScan[];
  recent_findings: AssetRecentFinding[];
}
