import { useQuery } from "@tanstack/react-query";
import { getDashboardOverview } from "@/services/dashboard";
import { QUERY_KEYS } from "@/shared/constants";

export function useDashboard() {
  return useQuery({
    queryKey: QUERY_KEYS.dashboard,
    queryFn: getDashboardOverview,
    refetchInterval: 30000,
  });
}
