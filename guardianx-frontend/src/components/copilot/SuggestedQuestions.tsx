import { Bot, Sparkles } from "lucide-react";

const SUGGESTIONS = [
  "Explain this CVE: CVE-2021-44228",
  "Show my critical vulnerabilities",
  "What are my top 5 risks?",
  "Find assets running PostgreSQL",
  "Generate a technical security summary",
  "Summarize today's scans",
];

interface Props {
  onSelect: (prompt: string) => void;
  disabled?: boolean;
}

export default function SuggestedQuestions({ onSelect, disabled }: Props) {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-6 text-center">
      <div className="rounded-2xl bg-cyan-500/10 p-5 text-cyan-400">
        <Bot size={40} />
      </div>

      <div>
        <h2 className="text-2xl font-bold text-white">
          How can I help secure your estate?
        </h2>
        <p className="mt-2 max-w-md text-sm text-slate-400">
          Ask about a CVE, a vulnerability, an asset&apos;s risk, today&apos;s
          scans, remediation, priorities, technical or executive summaries — or
          search your estate in plain English.
        </p>
      </div>

      <div className="grid w-full max-w-xl gap-2 sm:grid-cols-2">
        {SUGGESTIONS.map((suggestion) => (
          <button
            key={suggestion}
            type="button"
            disabled={disabled}
            onClick={() => onSelect(suggestion)}
            className="flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-900/60 px-4 py-3 text-left text-sm text-slate-300 transition hover:border-cyan-500/50 hover:text-cyan-200 disabled:opacity-50"
          >
            <Sparkles size={14} className="shrink-0 text-cyan-400" />
            {suggestion}
          </button>
        ))}
      </div>
    </div>
  );
}
