import { useState } from "react";

import { useFindingsAssignees, useUpdateFindingTriage } from "@/hooks/useFindings";
import { useToastContext } from "@/hooks/useToastContext";
import {
  Button,
  Input,
  Select,
  Textarea,
} from "@/shared/components";
import { findingStatusOrder } from "@/theme";
import type { FindingDetail, FindingStatus } from "@/types/finding";

interface Props {
  finding: FindingDetail;
}

export default function FindingTriageForm({ finding }: Props) {
  const { data: assignees = [] } = useFindingsAssignees();
  const updateTriage = useUpdateFindingTriage();
  const { success, error: toastError } = useToastContext();

  const [status, setStatus] = useState<FindingStatus>(finding.status);
  const [assigneeId, setAssigneeId] = useState<number | "">(
    finding.assigned_to ?? ""
  );
  const [dueDate, setDueDate] = useState(
    finding.due_date ? finding.due_date.slice(0, 10) : ""
  );
  const [notes, setNotes] = useState(finding.notes ?? "");

  const dirty =
    status !== finding.status ||
    assigneeId !== (finding.assigned_to ?? "") ||
    dueDate !== (finding.due_date ? finding.due_date.slice(0, 10) : "") ||
    notes !== (finding.notes ?? "");

  function handleSave() {
    const payload: {
      status?: FindingStatus;
      assignee_id?: number | null;
      notes?: string | null;
      due_date?: string | null;
    } = {};

    if (status !== finding.status) payload.status = status;
    if (assigneeId !== (finding.assigned_to ?? "")) {
      payload.assignee_id = assigneeId === "" ? null : assigneeId;
    }
    if (dueDate !== (finding.due_date ? finding.due_date.slice(0, 10) : "")) {
      payload.due_date = dueDate === "" ? null : `${dueDate}T23:59:59Z`;
    }
    if (notes !== (finding.notes ?? "")) {
      payload.notes = notes === "" ? null : notes;
    }

    if (Object.keys(payload).length === 0) return;

    updateTriage.mutate(
      { id: finding.id, payload },
      {
        onSuccess: () => {
          success("Finding triage updated.");
        },
        onError: () => {
          toastError("Failed to update finding triage.");
        },
      }
    );
  }

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="triage-status" className="mb-2 block text-sm text-slate-400">
            Status
          </label>
          <Select
            id="triage-status"
            value={status}
            onChange={(e) => setStatus(e.target.value as FindingStatus)}
            aria-label="Finding status"
          >
            {findingStatusOrder.map((level) => (
              <option key={level} value={level.toUpperCase()}>
                {level.toUpperCase().replace("_", " ")}
              </option>
            ))}
          </Select>
        </div>

        <div>
          <label htmlFor="triage-assignee" className="mb-2 block text-sm text-slate-400">
            Assignee
          </label>
          <Select
            id="triage-assignee"
            value={assigneeId}
            onChange={(e) =>
              setAssigneeId(
                e.target.value === "" ? "" : Number(e.target.value)
              )
            }
            aria-label="Finding assignee"
          >
            <option value="">Unassigned</option>
            {assignees.map((assignee) => (
              <option key={assignee.id} value={assignee.id}>
                {assignee.username}
              </option>
            ))}
          </Select>
        </div>
      </div>

      <div>
        <label htmlFor="triage-due" className="mb-2 block text-sm text-slate-400">
          Due Date
        </label>
        <Input
          id="triage-due"
          type="date"
          value={dueDate}
          onChange={(e) => setDueDate(e.target.value)}
        />
      </div>

      <div>
        <label htmlFor="triage-notes" className="mb-2 block text-sm text-slate-400">
          Notes
        </label>
        <Textarea
          id="triage-notes"
          rows={4}
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Analysis notes, remediation context, owner decisions..."
        />
      </div>

      <Button
        onClick={handleSave}
        disabled={!dirty || updateTriage.isPending}
        className="w-full"
      >
        {updateTriage.isPending ? "Saving..." : "Save Triage"}
      </Button>
    </div>
  );
}
