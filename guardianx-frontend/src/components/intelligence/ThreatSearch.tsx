import { ShieldCheck, Sparkles } from "lucide-react";
import type { KeyboardEvent } from "react";

import { Button, SearchInput } from "@/shared/components";
import { Badge } from "@/shared/components";

import { detectIocType, IOC_META } from "./ioc";

interface Props {
  value: string;
  loading: boolean;
  onChange: (value: string) => void;
  onSubmit: (value: string) => void;
}

export default function ThreatSearch({
  value,
  loading,
  onChange,
  onSubmit,
}: Props) {
  const detected = detectIocType(value);
  const canSubmit = detected !== null && !loading;

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Enter" && canSubmit) {
      onSubmit(value);
    }
  }

  return (
    <div className="panel panel-hover p-6">
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-4 lg:flex-row">
          <div className="flex-1">
            <SearchInput
              value={value}
              onChange={onChange}
              onKeyDown={handleKeyDown}
              placeholder="Search an IP, domain, URL or SHA256 hash…"
              ariaLabel="Indicator of compromise"
            />
          </div>

          <Button onClick={() => onSubmit(value)} disabled={!canSubmit}>
            <ShieldCheck size={16} className="mr-2 inline" />
            {loading ? "Analyzing…" : "Analyze"}
          </Button>
        </div>

        <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
          <Sparkles size={14} className="text-cyan-400/70" />
          <span>Auto-detected IOC type:</span>
          {detected ? (
            <Badge color="cyan">
              {IOC_META[detected].label} · {IOC_META[detected].description}
            </Badge>
          ) : (
            <span className="italic">
              Enter a value to auto-detect its type (IP · Domain · URL · SHA256).
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
