import { ShieldCheck, Search } from "lucide-react";
import type { KeyboardEvent } from "react";

import { Button, SearchInput, Select } from "@/shared/components";

import type { VirusTotalResourceType } from "@/types/virustotal";

const TYPE_OPTIONS: {
  value: VirusTotalResourceType;
  label: string;
  placeholder: string;
  hint: string;
}[] = [
  {
    value: "url",
    label: "URL",
    placeholder: "https://example.com",
    hint: "Check a website for phishing, malware and other threats.",
  },
  {
    value: "domain",
    label: "Domain",
    placeholder: "example.com",
    hint: "Check a domain's reputation across security vendors.",
  },
  {
    value: "ip",
    label: "IP Address",
    placeholder: "8.8.8.8",
    hint: "Check an IPv4 or IPv6 address reputation.",
  },
  {
    value: "file",
    label: "SHA256 File Hash",
    placeholder: "64-character SHA256 hash",
    hint: "Look up a file's hash across antivirus engines.",
  },
];

interface Props {
  type: VirusTotalResourceType;
  value: string;
  loading: boolean;
  onTypeChange: (type: VirusTotalResourceType) => void;
  onValueChange: (value: string) => void;
  onSubmit: () => void;
}

export default function VirusTotalLookupForm({
  type,
  value,
  loading,
  onTypeChange,
  onValueChange,
  onSubmit,
}: Props) {
  const active = TYPE_OPTIONS.find((option) => option.value === type);

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Enter" && value.trim()) {
      onSubmit();
    }
  }

  return (
    <div className="panel p-6">
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-4 lg:flex-row">
          <Select
            value={type}
            onChange={(event) =>
              onTypeChange(event.target.value as VirusTotalResourceType)
            }
            aria-label="Lookup type"
            className="lg:w-56"
          >
            {TYPE_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>

          <div className="flex-1">
            <SearchInput
              value={value}
              onChange={onValueChange}
              onKeyDown={handleKeyDown}
              placeholder={active?.placeholder ?? "Look up..."}
              ariaLabel="Value to look up"
            />
          </div>

          <Button onClick={onSubmit} disabled={loading || !value.trim()}>
            <ShieldCheck size={16} className="mr-2 inline" />
            {loading ? "Looking up..." : "Look Up"}
          </Button>
        </div>

        <div className="flex items-center gap-2 text-xs text-slate-500">
          <Search size={14} className="text-cyan-400/70" />
          {active?.hint}
        </div>
      </div>
    </div>
  );
}
