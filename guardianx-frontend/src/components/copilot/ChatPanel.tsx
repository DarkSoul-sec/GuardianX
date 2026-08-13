import { useEffect, useRef, type ReactNode } from "react";
import { motion } from "framer-motion";
import { Bot } from "lucide-react";

import CopilotBubble from "@/components/copilot/CopilotBubble";
import SuggestedQuestions from "@/components/copilot/SuggestedQuestions";

import type { ChatMessage } from "@/types/copilot";

interface Props {
  messages: ChatMessage[];
  isPending: boolean;
  onSelectSuggestion: (prompt: string) => void;
  composer: ReactNode;
}

function TypingIndicator() {
  return (
    <div className="flex w-full justify-start gap-3">
      <div className="mt-1 h-8 w-8 shrink-0 rounded-xl bg-cyan-500/10 p-2 text-cyan-400">
        <Bot size={16} />
      </div>
      <div className="rounded-2xl border border-slate-800 bg-slate-900 px-4 py-4">
        <div className="flex gap-1.5">
          {[0, 1, 2].map((index) => (
            <motion.span
              key={index}
              className="h-2 w-2 rounded-full bg-cyan-400"
              animate={{ opacity: [0.3, 1, 0.3] }}
              transition={{ duration: 1, repeat: Infinity, delay: index * 0.2 }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

export default function ChatPanel({
  messages,
  isPending,
  onSelectSuggestion,
  composer,
}: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, isPending]);

  return (
    <div className="flex h-[calc(100vh-16rem)] flex-col overflow-hidden rounded-2xl border border-slate-800 bg-slate-950">
      <div className="flex-1 space-y-4 overflow-y-auto p-6">
        {messages.length === 0 && !isPending ? (
          <SuggestedQuestions
            onSelect={onSelectSuggestion}
            disabled={isPending}
          />
        ) : (
          messages.map((message) => (
            <CopilotBubble key={message.id} message={message} />
          ))
        )}

        {isPending && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      <div className="space-y-3 border-t border-slate-800 bg-slate-950 p-4">
        {composer}
      </div>
    </div>
  );
}
