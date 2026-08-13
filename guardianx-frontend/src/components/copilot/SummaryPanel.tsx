import { Download, FileText } from "lucide-react";

import { Button } from "@/shared/components";
import { downloadTextFile } from "@/shared/utils/download";
import { useToastContext } from "@/hooks/useToastContext";

import type { ChatMessage } from "@/types/copilot";

interface Props {
  message: ChatMessage;
}

/**
 * Renders the latest assistant answer as a copyable, exportable report panel
 * for executive/technical/dashboard summaries. Reuses the markdown bubble for
 * rendering; this panel adds the export affordances and a report header.
 */
export default function SummaryPanel({ message }: Props) {
  const { success } = useToastContext();

  function handleExport() {
    const intent = message.intent ?? "assistant";
    const stamp = new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-");
    downloadTextFile(`guardianx-${intent}-${stamp}.md`, message.content);
    success("Report exported as Markdown.");
  }

  return (
    <div className="rounded-2xl border border-cyan-500/30 bg-gradient-to-br from-cyan-500/5 to-transparent p-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <FileText size={16} className="text-cyan-400" />
          <h3 className="text-sm font-bold text-white">
            {message.intent === "executive_summary"
              ? "Executive Summary"
              : message.intent === "technical_summary"
                ? "Technical Summary"
                : "Copilot Report"}
          </h3>
        </div>

        <Button
          variant="secondary"
          onClick={handleExport}
          className="!px-3 !py-1.5 text-xs"
          title="Export this report as Markdown"
        >
          <Download size={14} className="mr-1.5" />
          Export
        </Button>
      </div>
    </div>
  );
}
