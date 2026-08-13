import api from "./api";
import type {
  Asset,
  AssetDetails,
  CreateAssetDto,
  UpdateAssetDto,
} from "@/types/asset";
import type { ScanProfile } from "@/types/scan";

class AssetService {
  async getAssets(): Promise<Asset[]> {
    const { data } = await api.get<Asset[]>("/assets");
    return data;
  }

  async getAsset(id: number): Promise<AssetDetails> {
    const { data } = await api.get<AssetDetails>(`/assets/${id}`);
    return data;
  }

  async createAsset(payload: CreateAssetDto): Promise<Asset> {
    const { data } = await api.post<Asset>("/assets", payload);
    return data;
  }

  async updateAsset(id: number, payload: UpdateAssetDto): Promise<Asset> {
    const { data } = await api.patch<Asset>(`/assets/${id}`, payload);
    return data;
  }

  async deleteAsset(id: number): Promise<void> {
    await api.delete(`/assets/${id}`);
  }

  async runScan(assetId: number, scanProfile?: ScanProfile) {
    const { data } = await api.post("/scans", {
      asset_id: assetId,
      scanner: "NMAP",
      scan_profile: scanProfile,
    });

    return data;
  }
}

const assetService = new AssetService();

export default assetService;
