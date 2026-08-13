import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import AssetService from "@/services/assets";
import type {
  CreateAssetDto,
  UpdateAssetDto,
} from "@/types/asset";
import type { ScanProfile } from "@/types/scan";
import { QUERY_KEYS } from "@/shared/constants";

export function useAssets() {
  return useQuery({
    queryKey: QUERY_KEYS.assets,
    queryFn: AssetService.getAssets,
  });
}

export function useAsset(id: number) {
  return useQuery({
    queryKey: QUERY_KEYS.asset(id),
    queryFn: () => AssetService.getAsset(id),
    enabled: !!id,
  });
}

export function useCreateAsset() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateAssetDto) =>
      AssetService.createAsset(data),

    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.assets,
      });
    },
  });
}

export function useUpdateAsset() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: number;
      data: UpdateAssetDto;
    }) => AssetService.updateAsset(id, data),

    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.assets,
      });
    },
  });
}

export function useDeleteAsset() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: AssetService.deleteAsset,

    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.assets,
      });
    },
  });
}

export function useRunScan() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      assetId,
      scanProfile,
    }: {
      assetId: number;
      scanProfile?: ScanProfile;
    }) => AssetService.runScan(assetId, scanProfile),

    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.dashboard,
      });

      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.scans,
      });
    },
  });
}
