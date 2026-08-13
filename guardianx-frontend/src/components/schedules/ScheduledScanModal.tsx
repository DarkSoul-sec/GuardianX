import { useEffect, useState } from "react";
import { CalendarClock } from "lucide-react";

import { Button, Input, Modal, Select } from "@/shared/components";

import { useAssets } from "@/hooks/useAssets";
import { useCreateSchedule, useUpdateSchedule } from "@/hooks/useSchedules";
import { useToastContext } from "@/hooks/useToastContext";
import type {
  ScheduleCadence,
  ScheduledScan,
  ScheduleWeekDay,
} from "@/types/schedule";

interface Props {
  open: boolean;
  onClose: () => void;
  schedule?: ScheduledScan | null;
}

const CADENCES: { value: ScheduleCadence; label: string }[] = [
  { value: "DAILY", label: "Daily" },
  { value: "WEEKLY", label: "Weekly" },
  { value: "MONTHLY", label: "Monthly" },
];

const WEEK_DAYS: { value: ScheduleWeekDay; label: string }[] = [
  { value: "MON", label: "Monday" },
  { value: "TUE", label: "Tuesday" },
  { value: "WED", label: "Wednesday" },
  { value: "THU", label: "Thursday" },
  { value: "FRI", label: "Friday" },
  { value: "SAT", label: "Saturday" },
  { value: "SUN", label: "Sunday" },
];

export default function ScheduledScanModal({
  open,
  onClose,
  schedule,
}: Props) {
  const { data: assets = [], isLoading: assetsLoading } = useAssets();
  const createSchedule = useCreateSchedule();
  const updateSchedule = useUpdateSchedule();
  const { success, error } = useToastContext();

  const [assetId, setAssetId] = useState("");
  const [cadence, setCadence] = useState<ScheduleCadence>("DAILY");
  const [timeOfDay, setTimeOfDay] = useState("02:00");
  const [weekDay, setWeekDay] = useState<ScheduleWeekDay>("MON");
  const [monthDay, setMonthDay] = useState("1");
  const [enabled, setEnabled] = useState(true);

  useEffect(() => {
    if (!open) return;

    if (schedule) {
      setAssetId(String(schedule.asset_id));
      setCadence(schedule.cadence);
      setTimeOfDay(schedule.time_of_day);
      setWeekDay(schedule.week_day ?? "MON");
      setMonthDay(schedule.month_day != null ? String(schedule.month_day) : "1");
      setEnabled(schedule.enabled);
    } else {
      setAssetId("");
      setCadence("DAILY");
      setTimeOfDay("02:00");
      setWeekDay("MON");
      setMonthDay("1");
      setEnabled(true);
    }
  }, [open, schedule]);

  function buildDto() {
    return {
      asset_id: Number(assetId),
      cadence,
      time_of_day: timeOfDay,
      week_day: cadence === "WEEKLY" ? weekDay : null,
      month_day: cadence === "MONTHLY" ? Number(monthDay) : null,
      enabled,
    };
  }

  function handleSubmit() {
    if (!assetId) {
      error("Please select an asset to schedule.");
      return;
    }

    const dto = buildDto();

    if (schedule) {
      updateSchedule.mutate(
        { id: schedule.id, dto },
        {
          onSuccess: () => {
            success("Schedule updated.");
            onClose();
          },
          onError: () => {
            error("Failed to update schedule.");
          },
        }
      );
    } else {
      createSchedule.mutate(dto, {
        onSuccess: () => {
          success("Schedule created.");
          onClose();
        },
        onError: () => {
          error("Failed to create schedule.");
        },
      });
    }
  }

  const isPending = createSchedule.isPending || updateSchedule.isPending;

  return (
    <Modal open={open} onClose={onClose} titleId="schedule-modal-title">
      <div className="p-8">
        <div className="mb-8 flex items-center gap-3">
          <CalendarClock className="text-cyan-400" size={34} />
          <div>
            <h2 id="schedule-modal-title" className="text-3xl font-bold text-white">
              {schedule ? "Edit Schedule" : "New Schedule"}
            </h2>
            <p className="text-slate-400">
              Recurring vulnerability monitoring for an asset
            </p>
          </div>
        </div>

        {assetsLoading ? (
          <p className="py-6 text-slate-400">Loading assets...</p>
        ) : assets.length === 0 ? (
          <p className="py-6 text-slate-400">
            No assets available. Create an asset before scheduling scans.
          </p>
        ) : (
          <div className="space-y-4">
            <Select
              value={assetId}
              onChange={(e) => setAssetId(e.target.value)}
              aria-label="Select asset"
            >
              <option value="">Select an asset</option>
              {assets.map((asset) => (
                <option key={asset.id} value={asset.id}>
                  {asset.name} ({asset.ip_address || asset.domain || "no address"})
                </option>
              ))}
            </Select>

            <div className="grid grid-cols-2 gap-4">
              <Select
                value={cadence}
                onChange={(e) => setCadence(e.target.value as ScheduleCadence)}
                aria-label="Cadence"
              >
                {CADENCES.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Select>

              <Input
                type="time"
                value={timeOfDay}
                onChange={(e) => setTimeOfDay(e.target.value)}
                aria-label="Time of day (UTC)"
              />
            </div>

            {cadence === "WEEKLY" && (
              <Select
                value={weekDay}
                onChange={(e) => setWeekDay(e.target.value as ScheduleWeekDay)}
                aria-label="Day of week"
              >
                {WEEK_DAYS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Select>
            )}

            {cadence === "MONTHLY" && (
              <Input
                type="number"
                min={1}
                max={31}
                value={monthDay}
                onChange={(e) => setMonthDay(e.target.value)}
                aria-label="Day of month"
                placeholder="Day of month (1-31)"
              />
            )}

            <label className="flex items-center gap-3 text-sm text-slate-300">
              <input
                type="checkbox"
                checked={enabled}
                onChange={(e) => setEnabled(e.target.checked)}
                className="h-4 w-4 rounded accent-cyan-500"
              />
              Enabled
            </label>
          </div>
        )}

        <div className="mt-8 flex justify-end gap-4">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!assetId || isPending}
          >
            {isPending
              ? "Saving..."
              : schedule
                ? "Save Changes"
                : "Create Schedule"}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
