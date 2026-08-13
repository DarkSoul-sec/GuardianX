import api from "./api";
import type {
  CreateScanDto,
  Scan,
  ScanOperations,
  ScanResult,
} from "@/types/scan";

class ScanService {
  async getScans(): Promise<Scan[]> {
    const { data } = await api.get<Scan[]>("/scans");
    return data;
  }

  async getScanOperations(): Promise<ScanOperations> {
    const { data } = await api.get<ScanOperations>("/scans/operations");
    return data;
  }

  async getScan(id: number): Promise<Scan> {
    const { data } = await api.get<Scan>(`/scans/${id}`);
    return data;
  }

  async getScanResults(id: number): Promise<ScanResult[]> {
    const { data } = await api.get<ScanResult[]>(`/scans/${id}/results`);
    return data;
  }

  async startScan(dto: CreateScanDto): Promise<Scan> {
    const { data } = await api.post<Scan>("/scans", dto);
    return data;
  }

  async cancelScan(id: number): Promise<Scan> {
    const { data } = await api.post<Scan>(`/scans/${id}/cancel`);
    return data;
  }
}

const scanService = new ScanService();

export default scanService;
