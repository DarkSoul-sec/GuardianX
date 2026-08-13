import { Select } from "@/shared/components";

import { findingStatusOrder, severityOrder } from "@/theme";

interface Props {
  severity: string;
  status: string;
  asset: string;
  assigned: "" | "me" | "unassigned";
  sortBy: string;
  sortOrder: "asc" | "desc";
  assets: string[];
  onSeverity: (v: string) => void;
  onStatus: (v: string) => void;
  onAsset: (v: string) => void;
  onAssigned: (v: "" | "me" | "unassigned") => void;
  onSortBy: (v: string) => void;
  onSortOrder: (v: "asc" | "desc") => void;
}

export default function FindingFilters({
  severity,
  status,
  asset,
  assigned,
  sortBy,
  sortOrder,
  assets,
  onSeverity,
  onStatus,
  onAsset,
  onAssigned,
  onSortBy,
  onSortOrder,
}: Props) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      <div className="w-44">
        <Select
          value={severity}
          onChange={(e) => onSeverity(e.target.value)}
          aria-label="Filter by severity"
        >
          <option value="">All Severities</option>
          {severityOrder.map((level) => (
            <option key={level} value={level.toUpperCase()}>
              {level.toUpperCase()}
            </option>
          ))}
        </Select>
      </div>

      <div className="w-44">
        <Select
          value={status}
          onChange={(e) => onStatus(e.target.value)}
          aria-label="Filter by status"
        >
          <option value="">All Status</option>
          {findingStatusOrder.map((level) => (
            <option key={level} value={level.toUpperCase()}>
              {level.toUpperCase().replace("_", " ")}
            </option>
          ))}
        </Select>
      </div>

      <div className="w-48">
        <Select
          value={asset}
          onChange={(e) => onAsset(e.target.value)}
          aria-label="Filter by asset"
        >
          <option value="">All Assets</option>
          {assets.map((name) => (
            <option key={name} value={name}>
              {name}
            </option>
          ))}
        </Select>
      </div>

      <div className="w-44">
        <Select
          value={assigned}
          onChange={(e) =>
            onAssigned(e.target.value as "" | "me" | "unassigned")
          }
          aria-label="Filter by assignment"
        >
          <option value="">All Assignments</option>
          <option value="me">Assigned to me</option>
          <option value="unassigned">Unassigned</option>
        </Select>
      </div>

      <div className="w-44">
        <Select
          value={sortBy}
          onChange={(e) => onSortBy(e.target.value)}
          aria-label="Sort by"
        >
          <option value="created_at">Newest First</option>
          <option value="severity">Severity</option>
          <option value="title">Title</option>
          <option value="cve">CVE</option>
          <option value="status">Status</option>
          <option value="asset">Asset</option>
        </Select>
      </div>

      <div className="w-40">
        <Select
          value={sortOrder}
          onChange={(e) => onSortOrder(e.target.value as "asc" | "desc")}
          aria-label="Sort order"
        >
          <option value="desc">Descending</option>
          <option value="asc">Ascending</option>
        </Select>
      </div>
    </div>
  );
}
