import { useState } from "react";

import { useBulkUpdateFindingStatus } from "@/hooks/useFindings";
import { useToastContext } from "@/hooks/useToastContext";
import { Button, Select } from "@/shared/components";
import { findingStatusOrder } from "@/theme";
import type { FindingStatus } from "@/types/finding";

interface Props {
  selectedIds: number[];
  onClear: () => void;
}

export default function BulkTriageBar({ selectedIds, onClear }: Props) {
  const bulkUpdate = useBulkUpdateFindingStatus();
  const { success, error: toastError } = useToastContext();
  const [status, setStatus] = useState<FindingStatus | "">("");

  const pending = selectedIds.length > 0;

  function handleApply() {
    if (!status || selectedIds.length === 0) return;

    bulkUpdate.mutate(
      { ids: selectedIds, status },
      {
        onSuccess: (result) => {
          success(
            `${result.updated} finding${result.updated === 1 ? "" : "s"} updated to ${status.replace("_", " ")}.`
          );
          setStatus("");
          onClear();
        },
        onError: () => {
          toastError("Failed to update selected findings.");
        },
      }
    );
  }

  if (!pending) return null;

  return (
    <div className="flex flex-col gap-4 rounded-2xl border border-cyan-500/30 bg-cyan-950/20 p-4 md:flex-row md:items-center">
      <p className="text-sm text-cyan-200">
        <span className="font-semibold">{selectedIds.length}</span> selected
      </p>

      <div className="flex flex-1 flex-col gap-3 sm:flex-row md:max-w-md">
        <Select
          value={status}
          onChange={(e) => setStatus(e.target.value as FindingStatus | "")}
          aria-label="Bulk status"
          className="w-full"
        >
          <option value="">Set status...</option>
          {findingStatusOrder.map((level) => (
            <option key={level} value={level.toUpperCase()}>
              {level.toUpperCase().replace("_", " ")}
            </option>
          ))}
        </Select>
        <Button
          onClick={handleApply}
          disabled={!status || bulkUpdate.isPending}
        >
          {bulkUpdate.isPending ? "Applying..." : "Apply"}
        </Button>
        <Button variant="secondary" onClick={onClear} disabled={bulkUpdate.isPending}>
          Clear
        </Button>
      </div>
    </div>
  );
}
