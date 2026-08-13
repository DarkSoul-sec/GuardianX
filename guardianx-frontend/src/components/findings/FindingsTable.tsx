import { useNavigate } from "react-router-dom";
import { Sparkles, Wrench } from "lucide-react";

import DataTable from "@/shared/components/DataTable";
import type { Column } from "@/shared/components/DataTable";
import CvssBadge from "@/shared/components/CvssBadge";
import IconButton from "@/shared/components/IconButton";
import SeverityBadge from "@/shared/components/SeverityBadge";
import ServiceBadge from "@/shared/components/ServiceBadge";
import StatusBadge from "@/shared/components/StatusBadge";

import { findingDeepLink } from "@/shared/utils/copilotLinks";

import type { Finding } from "@/types/finding";

interface Props {
  findings: Finding[];
  selectedIds: Set<number>;
  onSelect: (id: number) => void;
  onToggleSelect: (id: number) => void;
  onToggleAll: (ids: number[]) => void;
}

function Checkbox({
  checked,
  onChange,
  label,
}: {
  checked: boolean;
  onChange: () => void;
  label: string;
}) {
  return (
    <label className="flex w-6 cursor-pointer items-center justify-center">
      <span className="sr-only">{label}</span>
      <input
        type="checkbox"
        checked={checked}
        onChange={onChange}
        className="h-4 w-4 cursor-pointer accent-cyan-500"
      />
    </label>
  );
}

export default function FindingsTable({
  findings,
  selectedIds,
  onSelect,
  onToggleSelect,
  onToggleAll,
}: Props) {
  const navigate = useNavigate();
  const allSelected =
    findings.length > 0 && findings.every((row) => selectedIds.has(row.id));

  function openCopilot(row: Finding, action: "explain_cve" | "remediation") {
    navigate("/copilot", {
      state: findingDeepLink({
        action,
        findingId: row.id,
        cve: row.cve,
        title: row.title,
      }),
    });
  }

  const columns: Column<Finding>[] = [
    {
      key: "select",
      title: "Select",
      headerRender: () => (
        <Checkbox
          checked={allSelected}
          onChange={() =>
            onToggleAll(findings.map((row) => row.id))
          }
          label="Select all visible findings"
        />
      ),
      render: (row) => (
        <Checkbox
          checked={selectedIds.has(row.id)}
          onChange={() => onToggleSelect(row.id)}
          label={`Select finding ${row.id}`}
        />
      ),
    },
    {
      key: "severity",
      title: "Severity",
      render: (row) => <SeverityBadge severity={row.severity} />,
    },
    {
      key: "cve",
      title: "CVE",
      render: (row) => row.cve ?? "-",
    },
    {
      key: "cvss",
      title: "CVSS",
      render: (row) => <CvssBadge score={row.cvss} />,
    },
    {
      key: "asset_name",
      title: "Asset",
      render: (row) => row.asset_name ?? "-",
    },
    {
      key: "affected_service",
      title: "Service",
      render: (row) => <ServiceBadge service={row.affected_service} />,
    },
    {
      key: "status",
      title: "Status",
      render: (row) => <StatusBadge status={row.status} />,
    },
    {
      key: "assigned_to_name",
      title: "Assignee",
      render: (row) =>
        row.assigned_to_name ?? (
          <span className="text-slate-500">Unassigned</span>
        ),
    },
    {
      key: "copilot",
      title: "Copilot",
      render: (row) => (
        <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
          <IconButton
            label={`Ask Copilot to explain ${row.cve ?? "this finding"}`}
            colorClass="bg-slate-800 hover:bg-cyan-700"
            disabled={!row.cve}
            onClick={() => openCopilot(row, "explain_cve")}
          >
            <Sparkles size={14} />
          </IconButton>
          <IconButton
            label={`Ask Copilot for remediation guidance`}
            colorClass="bg-slate-800 hover:bg-cyan-700"
            onClick={() => openCopilot(row, "remediation")}
          >
            <Wrench size={14} />
          </IconButton>
        </div>
      ),
    },
  ];

  return (
    <DataTable
      columns={columns}
      data={findings}
      rowKey={(row) => row.id}
      onRowClick={(row) => onSelect(row.id)}
      ariaLabel="Findings table"
    />
  );
}
