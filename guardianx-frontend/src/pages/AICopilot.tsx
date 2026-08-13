import { useCallback, useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import { Cpu, Eraser, Sparkles } from "lucide-react";

import ChatPanel from "@/components/copilot/ChatPanel";
import CopilotComposer from "@/components/copilot/CopilotComposer";
import QuickActions from "@/components/copilot/QuickActions";
import SummaryPanel from "@/components/copilot/SummaryPanel";
import type { CopilotAction } from "@/components/copilot/actions";

import { Button, PageHeader } from "@/shared/components";
import { useLocalStorage } from "@/shared/hooks/useLocalStorage";

import { useToastContext } from "@/hooks/useToastContext";
import {
  useClearCopilotMemory,
  useCopilotMemory,
  useCopilotProvider,
  useCopilotStream,
} from "@/hooks/useCopilot";
import type {
  ChatMessage,
  CopilotChatRequest,
  CopilotDeepLink,
  CopilotIntent,
  CopilotStreamEvent,
} from "@/types/copilot";

const STORAGE_KEY = "guardianx_copilot_messages";

function ProviderBadge() {
  const { data } = useCopilotProvider();

  if (!data) return null;

  return (
    <span className="flex items-center gap-2 rounded-full border border-slate-800 bg-slate-900 px-3 py-1.5 text-xs font-semibold text-slate-300">
      {data.built_in ? (
        <>
          <Sparkles size={14} className="text-cyan-400" />
          Built-in analysis
        </>
      ) : (
        <>
          <Cpu size={14} className="text-cyan-400" />
          {data.provider} · {data.model}
        </>
      )}
    </span>
  );
}

export default function AICopilot() {
  const location = useLocation();
  const [messages, setMessages] = useLocalStorage<ChatMessage[]>(
    STORAGE_KEY,
    []
  );
  const [input, setInput] = useState("");
  const [activeIntent, setActiveIntent] = useState<CopilotIntent | null>(null);
  const [streamingId, setStreamingId] = useState<string | null>(null);
  const [deepLink, setDeepLink] = useState<CopilotDeepLink | null>(
    () => (location.state as CopilotDeepLink | null) ?? null
  );
  const deepLinkSent = useRef(false);
  const abortRef = useRef<AbortController | null>(null);

  const stream = useCopilotStream();
  const memory = useCopilotMemory();
  const clearMemory = useClearCopilotMemory();
  const { success, error: toastError } = useToastContext();

  const isPending = stream.isPending || streamingId !== null;

  const patchMessage = useCallback(
    (id: string, patch: Partial<ChatMessage>) => {
      setMessages((previous) =>
        previous.map((message) =>
          message.id === id ? { ...message, ...patch } : message
        )
      );
    },
    [setMessages]
  );

  const handleStreamEvent = useCallback(
    (id: string, event: CopilotStreamEvent) => {
      if (event.type === "meta") {
        patchMessage(id, {
          intent: event.intent,
          provider: event.provider,
          model: event.model ?? null,
          context: event.context ?? null,
        });
        return;
      }

      if (event.type === "token") {
        setMessages((previous) =>
          previous.map((message) =>
            message.id === id
              ? { ...message, content: `${message.content}${event.content}` }
              : message
          )
        );
        return;
      }

      if (event.type === "done") {
        patchMessage(id, {
          content: event.content,
          context: event.context ?? null,
          results: event.results ?? null,
          streaming: false,
        });
        setStreamingId(null);
        return;
      }

      if (event.type === "error") {
        patchMessage(id, {
          content:
            "I could not generate an answer right now. Please check the Copilot configuration and try again.",
          error: true,
          streaming: false,
        });
        setStreamingId(null);
        toastError(event.message);
      }
    },
    [patchMessage, setMessages, toastError]
  );

  const submit = useCallback(
    (
      prompt: string,
      intent: CopilotIntent | null,
      entity?: CopilotDeepLink
    ) => {
      const userMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content: prompt,
      };
      const assistantId = crypto.randomUUID();
      const assistantMessage: ChatMessage = {
        id: assistantId,
        role: "assistant",
        content: "",
        streaming: true,
      };

      const request: CopilotChatRequest = { message: prompt };
      if (intent && intent !== "general") {
        request.type = intent;
      }
      if (entity?.assetId) request.asset_id = entity.assetId;
      if (entity?.findingId) request.finding_id = entity.findingId;
      if (entity?.cve) request.cve = entity.cve;

      setMessages((previous) => [
        ...previous,
        userMessage,
        assistantMessage,
      ]);
      setInput("");
      setStreamingId(assistantId);

      const controller = new AbortController();
      abortRef.current = controller;

      stream.mutate(
        {
          request,
          onEvent: (event) => handleStreamEvent(assistantId, event),
          signal: controller.signal,
        },
        {
          onError: () => {
            setStreamingId(null);
            patchMessage(assistantId, {
              content:
                "I could not generate an answer right now. Please check the Copilot configuration and try again.",
              error: true,
              streaming: false,
            });
            toastError("Copilot request failed. Please try again.");
          },
        }
      );
    },
    [handleStreamEvent, patchMessage, setMessages, stream, toastError]
  );

  useEffect(() => {
    if (!deepLink || deepLinkSent.current || isPending) return;
    deepLinkSent.current = true;
    setActiveIntent(deepLink.intent);
    submit(deepLink.prompt, deepLink.intent, deepLink);
    setDeepLink(null);
  }, [deepLink, isPending, submit]);

  function handleQuickAction(action: CopilotAction) {
    setActiveIntent(action.intent);
    setInput(action.prompt);
  }

  function handleSuggestion(prompt: string) {
    setActiveIntent(null);
    submit(prompt, null);
  }

  function handleSend() {
    const text = input.trim();
    if (!text || isPending) return;

    submit(text, activeIntent);
  }

  function handleClearConversation() {
    abortRef.current?.abort();
    setStreamingId(null);
    setMessages([]);
    clearMemory.mutate(undefined, {
      onSuccess: () => {
        success("Conversation cleared.");
      },
    });
  }

  const lastAssistant = [...messages]
    .reverse()
    .find((message) => message.role === "assistant" && !message.error);

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between gap-4">
        <PageHeader
          title="AI Security Copilot"
          subtitle="Ask questions about your assets, findings, scans, and posture."
        />
        <div className="flex items-center gap-2">
          {memory.data && memory.data.turns > 0 && (
            <span className="hidden items-center gap-2 rounded-full border border-slate-800 bg-slate-900 px-3 py-1.5 text-xs font-semibold text-slate-400 md:flex">
              {memory.data.turns} turn{memory.data.turns === 1 ? "" : "s"} in
              context
            </span>
          )}
          <Button
            variant="secondary"
            onClick={handleClearConversation}
            className="!px-3 !py-1.5 text-xs"
            title="Clear conversation and memory"
          >
            <Eraser size={14} className="mr-1.5" />
            Clear
          </Button>
          <ProviderBadge />
        </div>
      </div>

      {lastAssistant &&
        (lastAssistant.intent === "executive_summary" ||
          lastAssistant.intent === "technical_summary" ||
          lastAssistant.intent === "dashboard_insights") && (
          <SummaryPanel message={lastAssistant} />
        )}

      <ChatPanel
        messages={messages}
        isPending={isPending}
        onSelectSuggestion={handleSuggestion}
        composer={
          <div className="space-y-3">
            <QuickActions
              active={activeIntent}
              onSelect={handleQuickAction}
              disabled={isPending}
            />
            <CopilotComposer
              value={input}
              onChange={setInput}
              onSend={handleSend}
              onClear={() => {
                setInput("");
                setActiveIntent(null);
              }}
              disabled={isPending}
            />
          </div>
        }
      />
    </div>
  );
}
