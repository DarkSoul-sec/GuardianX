import { Download } from "lucide-react";

import { Button, SearchInput, Select } from "@/shared/components";

export interface ScanFilters {
  search: string;
  status: string;
  scanner: string;
}

interface Props {
  filters: ScanFilters;
  onChange: (filters: ScanFilters) => void;
  scanners: string[];
  onExport?: () => void;
}

export default function ScanFilterBar({ filters, onChange, scanners, onExport }: Props) {
  function update<K extends keyof ScanFilters>(key: K, value: ScanFilters[K]) {
    onChange({ ...filters, [key]: value });
  }

  return (
    <div className="flex flex-col gap-4 md:flex-row md:items-center">
      <div className="md:max-w-md md:flex-1">
        <SearchInput
          value={filters.search}
          onChange={(value) => update("search", value)}
          placeholder="Search scans, assets, engines..."
        />
      </div>

      <div className="grid grid-cols-2 gap-4 md:w-80">
        <Select
          value={filters.status}
          onChange={(e) => update("status", e.target.value)}
          aria-label="Filter by status"
        >
          <option value="">All statuses</option>
          <option value="RUNNING">Running</option>
          <option value="PENDING">Pending</option>
          <option value="COMPLETED">Completed</option>
          <option value="FAILED">Failed</option>
          <option value="CANCELLED">Cancelled</option>
        </Select>

        <Select
          value={filters.scanner}
          onChange={(e) => update("scanner", e.target.value)}
          aria-label="Filter by scanner engine"
        >
          <option value="">All engines</option>
          {scanners.map((scanner) => (
            <option key={scanner} value={scanner}>
              {scanner.toUpperCase()}
            </option>
          ))}
        </Select>
      </div>

      {onExport && (
        <Button variant="secondary" onClick={onExport}>
          <Download size={16} className="mr-2 inline" />
          Export CSV
        </Button>
      )}
    </div>
  );
}
