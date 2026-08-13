import { useQuery } from "@tanstack/react-query";

import ReportService from "@/services/reports";
import { QUERY_KEYS } from "@/shared/constants";

export function useExecutiveReport() {
  return useQuery({
    queryKey: QUERY_KEYS.executiveReport,
    queryFn: ReportService.getExecutiveReport,
    staleTime: 60_000,
  });
}

export function useAssetReport(assetId: number) {
  return useQuery({
    queryKey: QUERY_KEYS.assetReport(assetId),
    queryFn: () => ReportService.getAssetReport(assetId),
    enabled: !!assetId,
  });
}

export function useScanReport(scanId: number) {
  return useQuery({
    queryKey: QUERY_KEYS.scanReport(scanId),
    queryFn: () => ReportService.getScanReport(scanId),
    enabled: !!scanId,
  });
}
