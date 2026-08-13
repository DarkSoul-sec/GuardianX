import { useQuery } from "@tanstack/react-query";

import SecurityService from "@/services/security";
import { QUERY_KEYS } from "@/shared/constants";

/**
 * Whether the backend is running in local development mode with private
 * network scanning enabled (ALLOW_PRIVATE_NETWORK_SCANS=true).
 */
export function usePrivateNetworkScanningEnabled() {
  return useQuery({
    queryKey: QUERY_KEYS.securityConfig,
    queryFn: SecurityService.getConfig,
    staleTime: 60_000,
    retry: false,
  });
}