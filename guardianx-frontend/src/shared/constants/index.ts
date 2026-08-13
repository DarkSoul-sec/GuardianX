/**
 * Storage keys and React Query keys.
 */

export const STORAGE_KEYS = {
  ACCESS_TOKEN: "guardianx_access_token",
  REFRESH_TOKEN: "guardianx_refresh_token",
  THEME: "guardianx_theme",
} as const;

export const QUERY_KEYS = {
  dashboard: ["dashboard"] as const,
  assets: ["assets"] as const,
  asset: (id: number) => ["asset", id] as const,
  findings: ["findings"] as const,
  finding: (id: number) => ["finding", id] as const,
  findingStats: ["finding-stats"] as const,
  findingActivities: (id: number) => ["finding-activities", id] as const,
  findingAssignees: ["finding-assignees"] as const,
  scans: ["scans"] as const,
  scan: (id: number) => ["scan", id] as const,
  scanResults: (id: number) => ["scan-results", id] as const,
  scanOperations: ["scan-operations"] as const,
  schedules: ["schedules"] as const,
  reports: ["reports"] as const,
  executiveReport: ["reports", "executive"] as const,
  assetReport: (id: number) => ["reports", "asset", id] as const,
  scanReport: (id: number) => ["reports", "scan", id] as const,
  me: ["me"] as const,
  sessions: ["me", "sessions"] as const,
  notifications: ["notifications"] as const,
  unreadCount: ["notifications", "unread"] as const,
  copilotProvider: ["copilot", "provider"] as const,
  copilotMemory: ["copilot", "memory"] as const,
  virustotalLookup: ["virustotal", "lookup"] as const,
  virustotalStatus: ["virustotal", "integration", "status"] as const,
  securityConfig: ["security", "config"] as const,
  phishingAnalyze: ["phishing", "analyze"] as const,
  threatIntelStats: ["threat-intel", "stats"] as const,
  threatIntelTrending: ["threat-intel", "trending"] as const,
  threatIntelSearch: ["threat-intel", "search"] as const,
  threatIntelCve: ["threat-intel", "cve"] as const,
  threatIntelKev: ["threat-intel", "kev"] as const,
  threatIntelTechniques: ["threat-intel", "techniques"] as const,
  intelligenceLookup: ["intelligence", "lookup"] as const,
  intelligenceHistory: ["intelligence", "history"] as const,
  intelligenceStatus: ["intelligence", "status"] as const,
  socOverview: ["soc", "overview"] as const,
  socScanHealth: ["soc", "scan-health"] as const,
  socAlerts: ["soc", "alerts"] as const,
  socIncidents: ["soc", "incidents"] as const,
  activity: ["activity"] as const,
  activityLogins: ["activity", "logins"] as const,
} as const;

export const API_BASE_URL =
  import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000/api";
