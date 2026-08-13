import { useState } from "react";
import { BellRing, CheckCheck, ShieldQuestion } from "lucide-react";

import {
  Badge,
  Button,
  DataTable,
  Modal,
  PageHeader,
  type Column,
} from "@/shared/components";
import {
  useAlerts,
  useCreateIncident,
  useUpdateAlertStatus,
} from "@/hooks/useSoc";
import { useToastContext } from "@/hooks/useToastContext";
import { formatRelativeTime } from "@/shared/utils/format";
import type { Alert } from "@/types/soc";

function severityColor(severity: string) {
  const map: Record<string, "red" | "orange" | "yellow" | "green" | "gray"> = {
    CRITICAL: "red",
    HIGH: "orange",
    MEDIUM: "yellow",
    LOW: "green",
    INFO: "gray",
  };
  return map[severity] ?? "gray";
}

export default function Alerts() {
  const { success, error: showError } = useToastContext();
  const [statusFilter, setStatusFilter] = useState("");
  const [selected, setSelected] = useState<Alert | null>(null);
  const [incidentTitle, setIncidentTitle] = useState("");

  const { data, isLoading, isFetching } = useAlerts({
    status: statusFilter || undefined,
  });

  const updateStatus = useUpdateAlertStatus();
  const createIncident = useCreateIncident();

  const columns: Column<Alert>[] = [
    {
      key: "severity",
      title: "Severity",
      render: (alert) => (
        <Badge color={severityColor(alert.severity)}>{alert.severity}</Badge>
      ),
    },
    { key: "title", title: "Alert" },
    { key: "source", title: "Source" },
    {
      key: "created_at",
      title: "Detected",
      render: (alert) => (
        <span className="font-mono text-xs text-slate-400">
          {formatRelativeTime(alert.created_at)}
        </span>
      ),
    },
    {
      key: "status",
      title: "Status",
      render: (alert) => <span className="font-mono text-xs uppercase text-slate-400">{alert.status}</span>,
    },
    {
      key: "actions",
      title: "Actions",
      render: (alert) => (
        <div className="flex gap-2">
          <Button
            variant="secondary"
           
            onClick={(e) => {
              e.stopPropagation();
              if (statusFilter === "RESOLVED") return;
              updateStatus.mutate(
                { id: alert.id, status: "ACKNOWLEDGED" },
                { onSuccess: () => success("Alert acknowledged") }
              );
            }}
          >
            <CheckCheck size={14} /> Acknowledge
          </Button>
          <Button
            variant="secondary"
           
            onClick={(e) => {
              e.stopPropagation();
              setSelected(alert);
              setIncidentTitle(`Investigate: ${alert.title}`);
            }}
          >
            <ShieldQuestion size={14} /> Create Incident
          </Button>
        </div>
      ),
    },
  ];

  function handleCreateIncident() {
    if (!selected) return;

    createIncident.mutate(
      {
        title: incidentTitle,
        severity: selected.severity,
        alert_id: selected.id,
        asset_id: selected.asset_id,
        finding_id: selected.finding_id,
      },
      {
        onSuccess: () => {
          success("Incident created");
          setSelected(null);
        },
        onError: () => showError("Failed to create incident"),
      }
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Alert Center"
        subtitle="Triage detected alerts and promote them into incidents"
        action={
          <div className="flex items-center gap-2">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-sm text-slate-300"
            >
              <option value="">All statuses</option>
              <option value="OPEN">Open</option>
              <option value="ACKNOWLEDGED">Acknowledged</option>
              <option value="RESOLVED">Resolved</option>
            </select>
          </div>
        }
      />

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        loading={isLoading || isFetching}
        emptyText="No alerts found."
        rowKey={(alert) => alert.id}
        onRowClick={setSelected as never}
        ariaLabel="Alerts table"
      />

      <Modal
        open={Boolean(selected)}
        onClose={() => setSelected(null)}
        titleId="incident-modal-title"
      >
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <BellRing size={18} className="text-cyan-400" />
            <h2 id="incident-modal-title" className="font-display text-xl font-bold text-slate-100">
              Create Incident
            </h2>
          </div>

          <div>
            <label className="mb-1 block text-sm text-slate-400">Title</label>
            <input
              value={incidentTitle}
              onChange={(e) => setIncidentTitle(e.target.value)}
              className="w-full rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-slate-100"
            />
          </div>

          {selected && (
            <p className="text-sm text-slate-400">
              Promoting alert{" "}
              <span className="font-mono text-cyan-300">#{selected.id}</span>{" "}
              ({selected.severity}) to an incident.
            </p>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" onClick={() => setSelected(null)}>
              Cancel
            </Button>
            <Button onClick={handleCreateIncident} disabled={createIncident.isPending}>
              Create Incident
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}