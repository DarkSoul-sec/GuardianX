import { useEffect, useMemo, useState } from "react";
import { ShieldCheck } from "lucide-react";

import VirusTotalIntelPanel from "@/components/virustotal/VirusTotalIntelPanel";

import { Button, Select } from "@/shared/components";

import { useVirusTotalLookup } from "@/hooks/useVirusTotal";
import { extractIndicators, type ExtractedIndicator } from "@/shared/utils/indicators";

import type { VirusTotalResourceType } from "@/types/virustotal";

const TYPE_LABELS: Record<VirusTotalResourceType, string> = {
  url: "URL",
  domain: "Domain",
  ip: "IP Address",
  file: "SHA256 Hash",
};

interface Props {
  text: string;
}

export default function VirusTotalAnalyzeSection({ text }: Props) {
  const indicators = useMemo(() => extractIndicators(text), [text]);
  const [selected, setSelected] = useState<ExtractedIndicator | null>(null);
  const [active, setActive] = useState<ExtractedIndicator | null>(null);

  useEffect(() => {
    setSelected(indicators[0] ?? null);
    setActive(null);
  }, [indicators]);

  const query = useVirusTotalLookup(
    active?.type ?? "domain",
    active?.value ?? ""
  );

  if (indicators.length === 0) {
    return null;
  }

  function handleSelect(value: string) {
    const match = indicators.find((item) => item.value === value) ?? null;
    setSelected(match);
    setActive(null);
  }

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">
      <h3 className="mb-4 flex items-center gap-2 text-xl font-bold">
        <ShieldCheck size={18} className="text-cyan-400" />
        Analyze with VirusTotal
      </h3>

      <div className="flex flex-col gap-3 sm:flex-row">
        <Select
          value={selected?.value ?? ""}
          onChange={(event) => handleSelect(event.target.value)}
          aria-label="Indicator to analyze"
          className="flex-1"
        >
          {indicators.map((item) => (
            <option key={`${item.type}:${item.value}`} value={item.value}>
              {TYPE_LABELS[item.type]} · {item.value}
            </option>
          ))}
        </Select>

        <Button
          type="button"
          disabled={!selected || query.isFetching}
          onClick={() => setActive(selected)}
        >
          {query.isFetching ? "Analyzing..." : "Analyze"}
        </Button>
      </div>

      <div className="mt-4">
        <VirusTotalIntelPanel
          query={active?.value}
          data={query.data}
          loading={query.isLoading}
          error={query.error ?? null}
        />
      </div>
    </div>
  );
}
