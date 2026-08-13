import { useMutation, useQuery } from "@tanstack/react-query";

import CopilotService from "@/services/copilot";
import { QUERY_KEYS } from "@/shared/constants";
import type { CopilotChatRequest, CopilotStreamEvent } from "@/types/copilot";

export function useCopilotProvider() {
  return useQuery({
    queryKey: QUERY_KEYS.copilotProvider,
    queryFn: CopilotService.getProviderInfo,
    staleTime: 5 * 60_000,
  });
}

export function useCopilotChat() {
  return useMutation({
    mutationFn: (request: CopilotChatRequest) => CopilotService.chat(request),
  });
}

/**
 * Streams a Copilot answer over SSE. Returns a single `stream` callback that
 * forwards each parsed event; abort/cancel is exposed through `signal`.
 */
export function useCopilotStream() {
  return useMutation({
    mutationFn: ({
      request,
      onEvent,
      signal,
    }: {
      request: CopilotChatRequest;
      onEvent: (event: CopilotStreamEvent) => void;
      signal?: AbortSignal;
    }) => CopilotService.streamChat(request, onEvent, signal),
  });
}

export function useCopilotMemory() {
  return useQuery({
    queryKey: QUERY_KEYS.copilotMemory,
    queryFn: CopilotService.getMemoryStatus,
    refetchInterval: 30_000,
  });
}

export function useClearCopilotMemory() {
  return useMutation({
    mutationFn: () => CopilotService.clearMemory(),
  });
}
