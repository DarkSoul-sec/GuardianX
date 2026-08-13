import { Send, X } from "lucide-react";

import Button from "@/shared/components/Button";

import { cn } from "@/shared/utils/cn";

interface Props {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  onClear: () => void;
  disabled?: boolean;
  placeholder?: string;
}

export default function CopilotComposer({
  value,
  onChange,
  onSend,
  onClear,
  disabled = false,
  placeholder = "Ask about your security posture, a CVE, an asset, or scans...",
}: Props) {
  const canSend = value.trim().length > 0 && !disabled;

  function handleKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (canSend) onSend();
    }
  }

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900 p-3">
      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        rows={2}
        className="w-full resize-none bg-transparent p-2 text-sm text-white outline-none placeholder:text-slate-500"
      />

      <div className="flex items-center justify-between gap-3 border-t border-slate-800 pt-3">
        {value ? (
          <Button
            variant="secondary"
            onClick={onClear}
            className="!px-3 !py-1.5 text-xs"
            title="Clear input"
          >
            <X size={14} />
          </Button>
        ) : (
          <span className="text-xs text-slate-500">
            Enter to send · Shift+Enter for a new line
          </span>
        )}

        <Button
          onClick={onSend}
          disabled={!canSend}
          className={cn("flex items-center gap-2")}
        >
          <Send size={16} />
          Send
        </Button>
      </div>
    </div>
  );
}
