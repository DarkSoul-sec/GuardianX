import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import ScheduleService from "@/services/schedules";
import { QUERY_KEYS } from "@/shared/constants";
import type {
  CreateScheduleDto,
  UpdateScheduleDto,
} from "@/types/schedule";

export function useSchedules() {
  return useQuery({
    queryKey: QUERY_KEYS.schedules,
    queryFn: ScheduleService.getSchedules,
    refetchInterval: 30_000,
  });
}

export function useCreateSchedule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (dto: CreateScheduleDto) => ScheduleService.createSchedule(dto),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.schedules });
    },
  });
}

export function useUpdateSchedule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, dto }: { id: number; dto: UpdateScheduleDto }) =>
      ScheduleService.updateSchedule(id, dto),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.schedules });
    },
  });
}

export function useRunScheduleNow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => ScheduleService.runNow(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.schedules });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.scans });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.dashboard });
    },
  });
}

export function useDeleteSchedule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => ScheduleService.deleteSchedule(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.schedules });
    },
  });
}
