import api from "./api";
import {
  API_BASE_URL,
  STORAGE_KEYS,
} from "@/shared/constants";
import type {
  CopilotChatRequest,
  CopilotChatResponse,
  CopilotMemoryClearResponse,
  CopilotMemoryStatus,
  CopilotProviderInfo,
  CopilotStreamEvent,
} from "@/types/copilot";

class CopilotService {
  async chat(request: CopilotChatRequest): Promise<CopilotChatResponse> {
    const { data } = await api.post<CopilotChatResponse>(
      "/copilot/chat",
      request
    );
    return data;
  }

  async getProviderInfo(): Promise<CopilotProviderInfo> {
    const { data } = await api.get<CopilotProviderInfo>("/copilot/provider");
    return data;
  }

  async getMemoryStatus(): Promise<CopilotMemoryStatus> {
    const { data } = await api.get<CopilotMemoryStatus>("/copilot/memory");
    return data;
  }

  async clearMemory(): Promise<CopilotMemoryClearResponse> {
    const { data } = await api.delete<CopilotMemoryClearResponse>(
      "/copilot/memory"
    );
    return data;
  }

  /**
   * Stream a Copilot answer over SSE using fetch (axios cannot stream).
   * Parses `event:`/`data:` frames and dispatches parsed events to `onEvent`.
   */
  async streamChat(
    request: CopilotChatRequest,
    onEvent: (event: CopilotStreamEvent) => void,
    signal?: AbortSignal
  ): Promise<void> {
    const token = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);

    const response = await fetch(`${API_BASE_URL}/copilot/chat/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(request),
      signal,
    });

    if (!response.ok) {
      throw new Error(`Stream request failed (${response.status}).`);
    }

    const body = response.body;
    if (!body) {
      throw new Error("Streaming not supported by the browser.");
    }

    const reader = body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      let boundary = buffer.indexOf("\n\n");
      while (boundary !== -1) {
        const frame = buffer.slice(0, boundary);
        buffer = buffer.slice(boundary + 2);

        const event = parseSseFrame(frame);
        if (event) onEvent(event);

        boundary = buffer.indexOf("\n\n");
      }
    }
  }
}

function parseSseFrame(frame: string): CopilotStreamEvent | null {
  let eventType = "message";
  let data = "";

  for (const line of frame.split("\n")) {
    if (line.startsWith("event:")) {
      eventType = line.slice("event:".length).trim();
    } else if (line.startsWith("data:")) {
      data += line.slice("data:".length).trim();
    }
  }

  if (!data) return null;

  try {
    const parsed = JSON.parse(data) as Record<string, unknown>;
    return {
      ...parsed,
      type: eventType,
    } as CopilotStreamEvent;
  } catch {
    return null;
  }
}

export { parseSseFrame };

const copilotService = new CopilotService();
export default copilotService;
