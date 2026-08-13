import { memo, useState, type ComponentPropsWithoutRef } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Bot, Check, Copy, Download } from "lucide-react";

import CopilotAnswerMeta from "@/components/copilot/CopilotAnswerMeta";
import InsightCards from "@/components/copilot/InsightCards";
import { cn } from "@/shared/utils/cn";
import { copyText, downloadTextFile } from "@/shared/utils/download";
import { useToastContext } from "@/hooks/useToastContext";
import type { ChatMessage } from "@/types/copilot";

interface Props {
  message: ChatMessage;
}

function Link(props: ComponentPropsWithoutRef<"a">) {
  return (
    <a
      {...props}
      target="_blank"
      rel="noopener noreferrer"
      className="text-cyan-400 underline underline-offset-2"
    />
  );
}

function Code(props: ComponentPropsWithoutRef<"code">) {
  const first = Array.isArray(props.children)
    ? props.children[0]
    : props.children;
  const isBlock = typeof first === "string" && /^[\n`]/.test(first);
  if (isBlock) {
    return (
      <code
        className="block overflow-x-auto rounded-lg border border-slate-800 bg-slate-950 p-3 font-mono text-xs text-cyan-300"
        {...props}
      />
    );
  }
  return (
    <code
      className="rounded bg-slate-800 px-1.5 py-0.5 font-mono text-xs text-cyan-300"
      {...props}
    />
  );
}

function AnswerActions({ message }: Props) {
  const [copied, setCopied] = useState(false);
  const { success, error } = useToastContext();

  async function handleCopy() {
    const ok = await copyText(message.content);
    if (ok) {
      setCopied(true);
      success("Answer copied to clipboard.");
      window.setTimeout(() => setCopied(false), 2000);
    } else {
      error("Could not copy the answer.");
    }
  }

  function handleDownload() {
    const intent = message.intent ?? "assistant";
    const stamp = new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-");
    downloadTextFile(
      `guardianx-${intent}-${stamp}.md`,
      message.content
    );
    success("Answer exported as Markdown.");
  }

  return (
    <div className="mt-2 flex items-center gap-1">
      <button
        type="button"
        onClick={handleCopy}
        title="Copy answer"
        aria-label="Copy answer"
        className="rounded-lg p-1.5 text-slate-500 transition hover:bg-slate-800 hover:text-cyan-300"
      >
        {copied ? <Check size={13} /> : <Copy size={13} />}
      </button>
      <button
        type="button"
        onClick={handleDownload}
        title="Export as Markdown"
        aria-label="Export as Markdown"
        className="rounded-lg p-1.5 text-slate-500 transition hover:bg-slate-800 hover:text-cyan-300"
      >
        <Download size={13} />
      </button>
    </div>
  );
}

function CopilotBubbleBase({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <div
      className={cn(
        "flex w-full gap-3",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      {!isUser && (
        <div className="mt-1 h-8 w-8 shrink-0 rounded-xl bg-cyan-500/10 p-2 text-cyan-400">
          <Bot size={16} />
        </div>
      )}

      <div
        className={cn(
          "max-w-[85%] rounded-2xl border px-4 py-3",
          isUser
            ? "border-cyan-700 bg-cyan-600 text-white"
            : cn(
                "border-slate-800 bg-slate-900",
                message.error && "border-red-900/60 bg-red-950/30"
              )
        )}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap text-sm leading-relaxed">
            {message.content}
          </p>
        ) : (
          <div>
            <CopilotAnswerMeta message={message} />
            <div
              className={cn(
                "markdown-body text-sm leading-relaxed text-slate-300",
                message.error && "text-red-300"
              )}
            >
            <Markdown
              remarkPlugins={[remarkGfm]}
              components={{
                a: Link,
                code: Code,
                h1: (props) => (
                  <h1
                    className="mb-2 mt-3 text-lg font-bold text-white first:mt-0"
                    {...props}
                  />
                ),
                h2: (props) => (
                  <h2
                    className="mb-2 mt-3 text-base font-bold text-white first:mt-0"
                    {...props}
                  />
                ),
                h3: (props) => (
                  <h3
                    className="mb-2 mt-3 text-base font-bold text-white first:mt-0"
                    {...props}
                  />
                ),
                h4: (props) => (
                  <h4
                    className="mb-1 mt-2 text-sm font-bold text-white first:mt-0"
                    {...props}
                  />
                ),
                p: (props) => (
                  <p className="mb-2 last:mb-0" {...props} />
                ),
                ul: (props) => (
                  <ul className="mb-2 list-disc space-y-1 pl-5 last:mb-0" {...props} />
                ),
                ol: (props) => (
                  <ol className="mb-2 list-decimal space-y-1 pl-5 last:mb-0" {...props} />
                ),
                li: (props) => <li className="pl-1" {...props} />,
                strong: (props) => (
                  <strong className="font-bold text-white" {...props} />
                ),
                blockquote: (props) => (
                  <blockquote
                    className="mb-2 border-l-2 border-cyan-500 pl-3 italic text-slate-400"
                    {...props}
                  />
                ),
                table: (props) => (
                  <div className="mb-2 overflow-x-auto rounded-lg border border-slate-800">
                    <table className="min-w-full text-xs" {...props} />
                  </div>
                ),
                th: (props) => (
                  <th
                    className="border-b border-slate-800 bg-slate-950 px-3 py-2 text-left font-bold text-white"
                    {...props}
                  />
                ),
                td: (props) => (
                  <td
                    className="border-b border-slate-800 px-3 py-2 last:border-b-0"
                    {...props}
                  />
                ),
                hr: () => <hr className="my-3 border-slate-800" />,
              }}
            >
              {message.content}
            </Markdown>
            </div>
            {message.results && message.results.length > 0 && (
              <InsightCards results={message.results} />
            )}
            {!message.error && <AnswerActions message={message} />}
          </div>
        )}
      </div>
    </div>
  );
}

const CopilotBubble = memo(CopilotBubbleBase);
export default CopilotBubble;
