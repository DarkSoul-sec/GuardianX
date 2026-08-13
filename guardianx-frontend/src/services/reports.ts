import api from "./api";
import type { AssetReport, ExecutiveReport, TechnicalReport } from "@/types/report";

class ReportService {
  async getExecutiveReport(): Promise<ExecutiveReport> {
    const { data } = await api.get<ExecutiveReport>("/reports/executive");
    return data;
  }

  async getAssetReport(assetId: number): Promise<AssetReport> {
    const { data } = await api.get<AssetReport>(`/reports/assets/${assetId}`);
    return data;
  }

  async getScanReport(scanId: number): Promise<TechnicalReport> {
    const { data } = await api.get<TechnicalReport>(`/reports/scans/${scanId}`);
    return data;
  }
}

const reportService = new ReportService();

export default reportService;
