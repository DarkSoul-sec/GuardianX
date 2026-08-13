import api from "./api";
import type {
  Assignee,
  BulkStatusUpdate,
  BulkUpdateResult,
  FindingActivity,
  FindingDetail,
  FindingIntelligenceResponse,
  FindingListResponse,
  FindingQueryParams,
  FindingStats,
  FindingStatus,
  FindingTriageUpdate,
} from "@/types/finding";

class FindingService {
  async getFindings(params?: FindingQueryParams): Promise<FindingListResponse> {
    const { data } = await api.get<FindingListResponse>("/findings", { params });
    return data;
  }

  async getFinding(id: number): Promise<FindingDetail> {
    const { data } = await api.get<FindingDetail>(`/findings/${id}`);
    return data;
  }

  async getFindingIntelligence(id: number): Promise<FindingIntelligenceResponse> {
    const { data } = await api.get<FindingIntelligenceResponse>(
      `/findings/${id}/intelligence`
    );
    return data;
  }

  async getFindingStats(): Promise<FindingStats> {
    const { data } = await api.get<FindingStats>("/findings/stats");
    return data;
  }

  async getFindingActivities(id: number): Promise<FindingActivity[]> {
    const { data } = await api.get<FindingActivity[]>(
      `/findings/${id}/activities`
    );
    return data;
  }

  async getAssignees(): Promise<Assignee[]> {
    const { data } = await api.get<Assignee[]>("/findings/assignees");
    return data;
  }

  async updateStatus(id: number, status: FindingStatus): Promise<FindingDetail> {
    const { data } = await api.patch<FindingDetail>(`/findings/${id}/status`, {
      status,
    });
    return data;
  }

  async updateTriage(
    id: number,
    payload: FindingTriageUpdate
  ): Promise<FindingDetail> {
    const { data } = await api.patch<FindingDetail>(
      `/findings/${id}/triage`,
      payload
    );
    return data;
  }

  async bulkUpdateStatus(
    payload: BulkStatusUpdate
  ): Promise<BulkUpdateResult> {
    const { data } = await api.post<BulkUpdateResult>(
      "/findings/bulk-status",
      payload
    );
    return data;
  }

  async exportFindings(params?: FindingQueryParams): Promise<void> {
    const response = await api.get<Blob>("/findings/export", {
      params,
      responseType: "blob",
    });

    const data = response.data;
    const disposition = response.headers["content-disposition"] ?? "";
    const match = disposition.match(/filename="?([^";]+)"?/);
    const filename =
      match?.[1] ??
      `guardianx-findings-${new Date().toISOString().slice(0, 10)}.csv`;

    const url = URL.createObjectURL(data);
    const anchor = document.createElement("a");

    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    document.body.removeChild(anchor);
    URL.revokeObjectURL(url);
  }
}

const findingService = new FindingService();

export default findingService;
