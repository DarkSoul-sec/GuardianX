export type AlertStatus = "OPEN" | "ACKNOWLEDGED" | "RESOLVED";

export type IncidentStatus =
  | "OPEN"
  | "INVESTIGATING"
  | "MITIGATED"
  | "RESOLVED";

export type Severity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "INFO";

export interface Alert {
  id: number;
  user_id: number;
  alert_type: string;
  title: string;
  body: string | null;
  severity: string;
  source: string;
  finding_id: number | null;
  asset_id: number | null;
  status: AlertStatus;
  acknowledged_at: string | null;
  resolved_at: string | null;
  created_at: string;
}

export interface AlertList {
  items: Alert[];
  total: number;
  open: number;
}

export interface Incident {
  id: number;
  user_id: number;
  title: string;
  description: string | null;
  severity: Severity;
  status: IncidentStatus;
  asset_id: number | null;
  alert_id: number | null;
  finding_id: number | null;
  assignee_id: number | null;
  summary: string | null;
  resolved_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface IncidentList {
  items: Incident[];
  total: number;
  open: number;
}

export interface ActivityItem {
  id: number;
  user_id: number;
  action: string;
  entity_type: string | null;
  entity_id: number | null;
  detail: string | null;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
}

export interface ActivityList {
  items: ActivityItem[];
  total: number;
}

export interface LiveScan {
  scan_id: number;
  asset_name: string;
  status: string;
  started_at: string | null;
  elapsed_seconds: number | null;
}

export interface SocOverview {
  scans: {
    total: number;
    completed: number;
    failed: number;
    cancelled: number;
    running: number;
    pending: number;
    success_rate: number;
  };
  live_scans: LiveScan[];
  attack_surface_trend: Array<{ date: string; count: number }>;
  alerts: { open: number; critical: number };
  incidents: { open: number; total: number };
  recent_activity: ActivityItem[];
}

export interface ScanHealth {
  trend: Array<{ date: string; completed: number; failed: number }>;
}

export interface AlertSummary {
  open: number;
  acknowledged: number;
  critical: number;
}
