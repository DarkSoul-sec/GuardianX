import { useState } from "react";
import { CalendarClock, Pencil, Play, Plus, Trash2 } from "lucide-react";

import ScheduledScanModal from "@/components/schedules/ScheduledScanModal";
import { Badge, Button, Card, EmptyState, IconButton } from "@/shared/components";
import {
  useDeleteSchedule,
  useRunScheduleNow,
  useSchedules,
  useUpdateSchedule,
} from "@/hooks/useSchedules";
import { useToastContext } from "@/hooks/useToastContext";
import { formatRelativeTime } from "@/shared/utils/format";
import type { ScheduledScan } from "@/types/schedule";

const WEEK_DAY_LABELS: Record<string, string> = {
  MON: "Monday",
  TUE: "Tuesday",
  WED: "Wednesday",
  THU: "Thursday",
  FRI: "Friday",
  SAT: "Saturday",
  SUN: "Sunday",
};

function cadenceLabel(schedule: ScheduledScan): string {
  if (schedule.cadence === "WEEKLY") {
    const day = WEEK_DAY_LABELS[schedule.week_day ?? ""] ?? schedule.week_day;
    return `${day} at ${schedule.time_of_day} UTC`;
  }

  if (schedule.cadence === "MONTHLY") {
    return `Day ${schedule.month_day} at ${schedule.time_of_day} UTC`;
  }

  return `Daily at ${schedule.time_of_day} UTC`;
}

export default function ScheduledScans() {
  const { data = [], isLoading } = useSchedules();
  const updateSchedule = useUpdateSchedule();
  const runNow = useRunScheduleNow();
  const deleteSchedule = useDeleteSchedule();
  const { success, error: toastError } = useToastContext();

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<ScheduledScan | null>(null);

  function openCreate() {
    setEditing(null);
    setModalOpen(true);
  }

  function openEdit(schedule: ScheduledScan) {
    setEditing(schedule);
    setModalOpen(true);
  }

  function handleToggle(schedule: ScheduledScan) {
    updateSchedule.mutate(
      { id: schedule.id, dto: { enabled: !schedule.enabled } },
      {
        onSuccess: () => {
          success(
            `Schedule ${schedule.enabled ? "paused" : "resumed"} for ${schedule.asset_name ?? "asset"}.`
          );
        },
        onError: () => {
          toastError("Failed to update schedule.");
        },
      }
    );
  }

  function handleRunNow(schedule: ScheduledScan) {
    runNow.mutate(schedule.id, {
      onSuccess: () => {
        success(`Scan launched for ${schedule.asset_name ?? "asset"}.`);
      },
      onError: () => {
        toastError("Failed to launch scheduled scan.");
      },
    });
  }

  function handleDelete(schedule: ScheduledScan) {
    deleteSchedule.mutate(schedule.id, {
      onSuccess: () => {
        success(`Schedule for ${schedule.asset_name ?? "asset"} deleted.`);
      },
      onError: () => {
        toastError("Failed to delete schedule.");
      },
    });
  }

  return (
    <Card className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <CalendarClock size={22} className="text-cyan-400" />
          <div>
            <h3 className="text-lg font-semibold text-white">
              Scheduled Scans
            </h3>
            <p className="text-sm text-slate-400">
              Recurring monitoring runs on your assets
            </p>
          </div>
        </div>
        <Button onClick={openCreate}>
          <Plus size={16} className="mr-2 inline" />
          Add Schedule
        </Button>
      </div>

      {isLoading ? (
        <p className="py-8 text-center text-slate-400">
          Loading schedules...
        </p>
      ) : data.length === 0 ? (
        <EmptyState
          title="No scheduled scans"
          description="Create a recurring scan to continuously monitor an asset."
          icon={<CalendarClock size={40} />}
          action={
            <Button onClick={openCreate}>
              <Plus size={16} className="mr-2 inline" />
              Create Schedule
            </Button>
          }
        />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-800 text-xs uppercase tracking-wide text-slate-500">
                <th className="pb-3 pr-4">Asset</th>
                <th className="pb-3 pr-4">Schedule</th>
                <th className="pb-3 pr-4">Next Run</th>
                <th className="pb-3 pr-4">Last Run</th>
                <th className="pb-3 pr-4">Status</th>
                <th className="pb-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {data.map((schedule) => (
                <tr
                  key={schedule.id}
                  className="border-b border-slate-800/60 last:border-0"
                >
                  <td className="py-3 pr-4 font-medium text-white">
                    {schedule.asset_name ?? `Asset #${schedule.asset_id}`}
                  </td>
                  <td className="py-3 pr-4 text-slate-300">
                    <p>{cadenceLabel(schedule)}</p>
                    <p className="text-xs text-slate-500">{schedule.scanner}</p>
                  </td>
                  <td className="py-3 pr-4 text-slate-300">
                    {schedule.enabled
                      ? formatRelativeTime(schedule.next_run_at)
                      : "-"}
                  </td>
                  <td className="py-3 pr-4 text-slate-300">
                    {formatRelativeTime(schedule.last_run_at)}
                  </td>
                  <td className="py-3 pr-4">
                    {schedule.enabled ? (
                      <Badge className="bg-emerald-500/15 text-emerald-400">
                        Active
                      </Badge>
                    ) : (
                      <Badge className="bg-slate-500/15 text-slate-400">
                        Paused
                      </Badge>
                    )}
                  </td>
                  <td className="py-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        role="switch"
                        aria-checked={schedule.enabled}
                        aria-label={`${schedule.enabled ? "Pause" : "Resume"} schedule for ${schedule.asset_name ?? "asset"}`}
                        onClick={() => handleToggle(schedule)}
                        className={`relative h-5 w-9 rounded-full transition ${
                          schedule.enabled ? "bg-cyan-500" : "bg-slate-700"
                        }`}
                      >
                        <span
                          className={`absolute top-0.5 h-4 w-4 rounded-full bg-white transition ${
                            schedule.enabled ? "left-4" : "left-0.5"
                          }`}
                        />
                      </button>
                      <IconButton
                        label="Run now"
                        onClick={() => handleRunNow(schedule)}
                      >
                        <Play size={16} />
                      </IconButton>
                      <IconButton
                        label="Edit"
                        onClick={() => openEdit(schedule)}
                      >
                        <Pencil size={16} />
                      </IconButton>
                      <IconButton
                        label="Delete"
                        onClick={() => handleDelete(schedule)}
                      >
                        <Trash2 size={16} />
                      </IconButton>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <ScheduledScanModal
        open={modalOpen}
        onClose={() => {
          setModalOpen(false);
          setEditing(null);
        }}
        schedule={editing}
      />
    </Card>
  );
}
