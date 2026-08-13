import { useState } from "react";
import { ShieldHalf, Trash2 } from "lucide-react";

import {
  Badge,
  Button,
  DataTable,
  Drawer,
  PageHeader,
  type Column,
} from "@/shared/components";
import { useDeleteIncident, useIncidents, useUpdateIncident } from "@/hooks/useSoc";
import { useToastContext } from "@/hooks/useToastContext";
import { formatRelativeTime } from "@/shared/utils/format";
import type { Incident } from "@/types/soc";

const STATUS_COLORS: Record<string, "red" | "yellow" | "blue" | "green" | "gray"> = {
  OPEN: "red",
  INVESTIGATING: "yellow",
  MITIGATED: "blue",
  RESOLVED: "green",
};

const INCIDENT_STATUSES = ["OPEN", "INVESTIGATING", "MITIGATED", "RESOLVED"];

export default function Incidents() {
  const { success, error: showError } = useToastContext();
  const [selected, setSelected] = useState<Incident | null>(null);
  const [statusFilter, setStatusFilter] = useState("");

  const { data, isLoading } = useIncidents({ status: statusFilter || undefined });
  const updateIncident = useUpdateIncident();
  const deleteIncident = useDeleteIncident();

  const columns: Column<Incident>[] = [
    {
      key: "title",
      title: "Incident",
      render: (incident) => (
        <div>
          <p className="font-semibold text-slate-100">{incident.title}</p>
          {incident.alert_id && (
            <p className="font-mono text-[11px] text-slate-500">
              from alert #{incident.alert_id}
            </p>
          )}
        </div>
      ),
    },
    {
      key: "severity",
      title: "Severity",
      render: (incident) => (
        <Badge
          color={
            incident.severity === "CRITICAL"
              ? "red"
              : incident.severity === "HIGH"
                ? "orange"
                : incident.severity === "MEDIUM"
                  ? "yellow"
                  : "green"
          }
        >
          {incident.severity}
        </Badge>
      ),
    },
    {
      key: "status",
      title: "Status",
      render: (incident) => (
        <Badge color={STATUS_COLORS[incident.status] ?? "gray"}>
          {incident.status}
        </Badge>
      ),
    },
    {
      key: "created_at",
      title: "Opened",
      render: (incident) => (
        <span className="font-mono text-xs text-slate-400">
          {formatRelativeTime(incident.created_at)}
        </span>
      ),
    },
  ];

  function handleStatusChange(status: string) {
    if (!selected) return;
    updateIncident.mutate(
      { id: selected.id, payload: { status } },
      {
        onSuccess: (updated) => {
          setSelected(updated);
          success(`Incident status → ${status}`);
        },
        onError: () => showError("Failed to update incident"),
      }
    );
  }

  function handleDelete() {
    if (!selected) return;
    deleteIncident.mutate(selected.id, {
      onSuccess: () => {
        success("Incident deleted");
        setSelected(null);
      },
      onError: () => showError("Failed to delete incident"),
    });
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Incidents"
        subtitle="Investigations driven from alerts and findings"
        action={
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-sm text-slate-300"
          >
            <option value="">All statuses</option>
            <option value="OPEN">Open</option>
            <option value="INVESTIGATING">Investigating</option>
            <option value="MITIGATED">Mitigated</option>
            <option value="RESOLVED">Resolved</option>
          </select>
        }
      />

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        loading={isLoading}
        emptyText="No incidents yet."
        rowKey={(incident) => incident.id}
        onRowClick={setSelected}
        ariaLabel="Incidents table"
      />

      <Drawer open={Boolean(selected)} onClose={() => setSelected(null)}>
        {selected && (
          <div className="space-y-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="font-mono text-xs uppercase tracking-widest text-cyan-400">
                  Incident #{selected.id}
                </p>
                <h2 className="mt-2 font-display text-2xl font-bold text-slate-50">
                  {selected.title}
                </h2>
              </div>
              <Button variant="danger" onClick={handleDelete}>
                <Trash2 size={14} />
              </Button>
            </div>

            {selected.description && (
              <p className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 text-sm text-slate-300">
                {selected.description}
              </p>
            )}

            <div className="flex items-center justify-between gap-2">
              <div>
                <p className="eyebrow mb-1">Severity</p>
                <Badge color="red">{selected.severity}</Badge>
              </div>
              <div className="text-right">
                <p className="eyebrow mb-1">Opened</p>
                <p className="font-mono text-sm text-slate-300">
                  {formatRelativeTime(selected.created_at)}
                </p>
              </div>
            </div>

            <div>
              <p className="eyebrow mb-2 flex items-center gap-2">
                <ShieldHalf size={14} /> Update status
              </p>
              <div className="flex flex-wrap gap-2">
                {INCIDENT_STATUSES.map((status) => (
                  <Button
                    key={status}
                    variant={selected.status === status ? "primary" : "secondary"}
                   
                    onClick={() => handleStatusChange(status)}
                    disabled={updateIncident.isPending}
                  >
                    {status}
                  </Button>
                ))}
              </div>
            </div>

            {selected.summary && (
              <div>
                <p className="eyebrow mb-1">Summary</p>
                <p className="text-sm text-slate-300">{selected.summary}</p>
              </div>
            )}
          </div>
        )}
      </Drawer>
    </div>
  );
}