import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import UserService from "@/services/users";
import { QUERY_KEYS } from "@/shared/constants";
import type { ChangePasswordDto, UpdateProfileDto } from "@/types/user";

export function useMe() {
  return useQuery({
    queryKey: QUERY_KEYS.me,
    queryFn: UserService.getMe,
  });
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (dto: UpdateProfileDto) => UserService.updateProfile(dto),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.me });
    },
  });
}

export function useChangePassword() {
  return useMutation({
    mutationFn: (dto: ChangePasswordDto) => UserService.changePassword(dto),
  });
}

export function useSessions() {
  return useQuery({
    queryKey: QUERY_KEYS.sessions,
    queryFn: UserService.listSessions,
  });
}

export function useRevokeSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (sessionId: number) => UserService.revokeSession(sessionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.sessions });
    },
  });
}

export function useRevokeAllSessions() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => UserService.revokeAllSessions(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.sessions });
    },
  });
}
