import { Flame, Search, X } from "lucide-react";
import type { KeyboardEvent } from "react";

import { Button, Input, SearchInput, Select } from "@/shared/components";
import type { ThreatIntelSearchFilters } from "@/types/threat-intel";

const CURRENT_YEAR = new Date().getFullYear();

const YEAR_OPTIONS = Array.from({ length: 8 }, (_, index) =>
  String(CURRENT_YEAR - index)
);

interface Props {
  filters: ThreatIntelSearchFilters;
  searching: boolean;
  onChange: (filters: ThreatIntelSearchFilters) => void;
  onSubmit: () => void;
  onReset: () => void;
}

export default function CveSearchForm({
  filters,
  searching,
  onChange,
  onSubmit,
  onReset,
}: Props) {
  function update(patch: Partial<ThreatIntelSearchFilters>) {
    onChange({ ...filters, ...patch });
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Enter") {
      onSubmit();
    }
  }

  return (
    <div className="panel p-6">
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-4 lg:flex-row">
          <div className="flex-1">
            <SearchInput
              value={filters.q}
              onChange={(value) => update({ q: value })}
              onKeyDown={handleKeyDown}
              placeholder="Search CVEs, products, vendors..."
              ariaLabel="Search CVEs"
            />
          </div>

          <Select
            value={filters.severity}
            onChange={(event) => update({ severity: event.target.value })}
            aria-label="Severity filter"
            className="lg:w-44"
          >
            <option value="">All severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </Select>
          <Input
            value={filters.vendor}
            onChange={(event) => update({ vendor: event.target.value })}
            placeholder="Vendor filter"
            aria-label="Vendor filter"
            className="lg:w-44"
          />
          <Select
            value={filters.sort}
            onChange={(event) => update({ sort: event.target.value as ThreatIntelSearchFilters["sort"] })}
            aria-label="Sort CVEs"
            className="lg:w-44"
          >
            <option value="published">Recently published</option>
            <option value="epss">Highest EPSS</option>
            <option value="risk">Highest GuardianX risk</option>
          </Select>

          <Select
            value={filters.year}
            onChange={(event) => update({ year: event.target.value })}
            aria-label="Year filter"
            className="lg:w-32"
          >
            <option value="">Any year</option>
            {YEAR_OPTIONS.map((year) => (
              <option key={year} value={year}>
                {year}
              </option>
            ))}
          </Select>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-4">
          <button
            type="button"
            onClick={() => update({ exploited: !filters.exploited })}
            aria-pressed={filters.exploited}
            className={`flex items-center gap-2 rounded-lg border px-3 py-2 text-sm font-semibold transition ${
              filters.exploited
                ? "border-rose-500/50 bg-rose-500/10 text-rose-300"
                : "border-slate-800 bg-slate-900 text-slate-300 hover:border-slate-700"
            }`}
          >
            <Flame size={16} />
            Actively exploited only (CISA KEV)
          </button>

          <div className="flex items-center gap-2">
            <Button variant="secondary" onClick={onReset} disabled={searching}>
              <X size={16} className="mr-2 inline" />
              Reset
            </Button>
            <Button onClick={onSubmit} disabled={searching}>
              <Search size={16} className="mr-2 inline" />
              {searching ? "Searching..." : "Search"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
