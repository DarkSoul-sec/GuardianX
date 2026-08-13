import {
  COPILOT_ACTIONS,
  type CopilotAction,
} from "./actions";

import type { CopilotIntent } from "@/types/copilot";

interface Props {
  active: CopilotIntent | null;
  onSelect: (action: CopilotAction) => void;
  disabled?: boolean;
}

export default function QuickActions({ active, onSelect, disabled }: Props) {
  return (
    <div className="flex flex-wrap gap-2">
      {COPILOT_ACTIONS.map((action) => {
        const Icon = action.icon;
        const isActive = action.intent === active;

        return (
          <button
            key={action.intent}
            type="button"
            disabled={disabled}
            onClick={() => onSelect(action)}
            className={
              isActive
                ? "flex items-center gap-2 rounded-xl border border-cyan-600 bg-cyan-600/15 px-3 py-2 text-sm font-semibold text-cyan-300 transition"
                : "flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-900 px-3 py-2 text-sm font-semibold text-slate-300 transition hover:border-slate-700 hover:bg-slate-800"
            }
          >
            <Icon size={16} className={isActive ? "text-cyan-400" : "text-slate-500"} />
            {action.label}
          </button>
        );
      })}
    </div>
  );
}
