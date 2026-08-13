import {
  AlertTriangle,
  ClipboardList,
  Crosshair,
  FileWarning,
  LogIn,
  LogOut,
  Radar,
  ScanLine,
  ShieldAlert,
  ShieldCheck,
  ShieldX,
  Server,
  Settings,
  Trash2,
  UserPlus,
  type LucideIcon,
} from "lucide-react";

interface ActivityMeta {
  icon: LucideIcon;
  label: string;
}

const ACTIONS: Record<string, ActivityMeta> = {
  login: { icon: LogIn, label: "Signed in" },
  logout: { icon: LogOut, label: "Signed out" },
  asset_created: { icon: Server, label: "Asset created" },
  asset_updated: { icon: Server, label: "Asset updated" },
  asset_deleted: { icon: Trash2, label: "Asset deleted" },
  scan_started: { icon: ScanLine, label: "Scan started" },
  scan_completed: { icon: ShieldCheck, label: "Scan completed" },
  scan_failed: { icon: ShieldX, label: "Scan failed" },
  scan_cancelled: { icon: ShieldX, label: "Scan cancelled" },
  finding_opened: { icon: AlertTriangle, label: "Finding opened" },
  finding_closed: { icon: ShieldCheck, label: "Finding resolved" },
  finding_assigned: { icon: UserPlus, label: "Finding assigned" },
  threat_search: { icon: Crosshair, label: "Threat search" },
  vt_lookup: { icon: Radar, label: "VirusTotal lookup" },
  intelligence_search: { icon: Radar, label: "Intelligence lookup" },
  config_updated: { icon: Settings, label: "Configuration updated" },
  user_created: { icon: UserPlus, label: "User created" },
  role_changed: { icon: Settings, label: "Role changed" },
  incident_created: { icon: ClipboardList, label: "Incident created" },
  incident_updated: { icon: ClipboardList, label: "Incident updated" },
  system: { icon: ShieldAlert, label: "System event" },
};

export function getActivityMeta(action: string): ActivityMeta {
  return ACTIONS[action] ?? { icon: FileWarning, label: "Activity" };
}
