import { Fingerprint, Search } from "lucide-react";
import type { KeyboardEvent } from "react";

import { Button, SearchInput } from "@/shared/components";

interface Props {
  value: string;
  loading: boolean;
  onValueChange: (value: string) => void;
  onSubmit: () => void;
}

export default function PhishingAnalysisForm({
  value,
  loading,
  onValueChange,
  onSubmit,
}: Props) {
  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Enter" && value.trim()) {
      onSubmit();
    }
  }

  return (
    <div className="panel p-6">
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-4 lg:flex-row">
          <div className="flex-1">
            <SearchInput
              value={value}
              onChange={onValueChange}
              onKeyDown={handleKeyDown}
              placeholder="https://example.com/login"
              ariaLabel="URL to analyze"
            />
          </div>

          <Button onClick={onSubmit} disabled={loading || !value.trim()}>
            <Fingerprint size={16} className="mr-2 inline" />
            {loading ? "Analyzing..." : "Analyze URL"}
          </Button>
        </div>

        <div className="flex items-center gap-2 text-xs text-slate-500">
          <Search size={14} className="text-cyan-400/70" />
          Detects phishing indicators: URL structure, typosquatting, domain age,
          SSL, DNS, VirusTotal reputation, blacklists and suspicious keywords.
        </div>
      </div>
    </div>
  );
}
