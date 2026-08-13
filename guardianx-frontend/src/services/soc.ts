import api from "./api";
import type {
  ActivityList,
  Alert,
  AlertList,
  Incident,
  IncidentList,
  ScanHealth,
  SocOverview,
} from "@/types/soc";

export async function getSocOverview(): Promise<SocOverview> {
  const response = await api.get<SocOverview>("/soc/overview");
  return response.data;
}

export async function getScanHealth(days = 14): Promise<ScanHealth> {
  const response = await api.get<ScanHealth>("/soc/scans/health", {
    params: { days },
  });
  return response.data;
}

export async function getAlerts(params?: {
  status?: string;
  severity?: string;
  limit?: number;
  offset?: number;
}): Promise<AlertList> {
  const response = await api.get<AlertList>("/soc/alerts", { params });
  return response.data;
}

export async function updateAlertStatus(
  alertId: number,
  status: string
): Promise<Alert> {
  const response = await api.patch<Alert>(`/soc/alerts/${alertId}`, { status });
  return response.data;
}

export async function getIncidents(params?: {
  status?: string;
  severity?: string;
  limit?: number;
  offset?: number;
}): Promise<IncidentList> {
  const response = await api.get<IncidentList>("/soc/incidents", { params });
  return response.data;
}

export async function createIncident(payload: {
  title: string;
  description?: string | null;
  severity?: string;
  asset_id?: number | null;
  alert_id?: number | null;
  finding_id?: number | null;
  assignee_id?: number | null;
}): Promise<Incident> {
  const response = await api.post<Incident>("/soc/incidents", payload);
  return response.data;
}

export async function updateIncident(
  incidentId: number,
  payload: {
    status?: string;
    assignee_id?: number;
    summary?: string;
  }
): Promise<Incident> {
  const response = await api.patch<Incident>(
    `/soc/incidents/${incidentId}`,
    payload
  );
  return response.data;
}

export async function deleteIncident(incidentId: number): Promise<void> {
  await api.delete(`/soc/incidents/${incidentId}`);
}

export async function getActivity(limit = 50): Promise<ActivityList> {
  const response = await api.get<ActivityList>("/activity", {
    params: { limit },
  });
  return response.data;
}

export async function getLoginHistory(limit = 20): Promise<ActivityList> {
  const response = await api.get<ActivityList>("/activity/logins", {
    params: { limit },
  });
  return response.data;
}
