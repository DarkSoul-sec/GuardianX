export type ScanStatus =
  | "PENDING"
  | "RUNNING"
  | "COMPLETED"
  | "FAILED"
  | "CANCELLED";

export type ScanProfile = "standard" | "full";

export interface Scan {
  id: number;
  asset_id: number;
  asset_name: string | null;
  status: ScanStatus;
  scanner: string;
  scan_profile: ScanProfile;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
  finding_count: number;
}

export interface ScanResult {
  id: number;
  port: number;
  protocol: string;
  state: string;
  service: string | null;
  product: string | null;
  version: string | null;
  is_ssl: boolean;
}

export interface CreateScanDto {
  asset_id: number;
  scan_profile?: ScanProfile;
}

export interface ExecutorStatus {
  max_workers: number;
  queued: number;
  running: number;
  idle_workers: number;
  closed: boolean;
}

export interface ScanOperations {
  executor: ExecutorStatus;
  counts: Record<string, number>;
  total: number;
}
