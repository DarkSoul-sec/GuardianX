import { motion } from "framer-motion";
import { Bot, Cpu, Link2 } from "lucide-react";

import type { ChatMessage, CopilotIntent } from "@/types/copilot";

const INTENT_LABELS: Record<CopilotIntent, string> = {
  explain_cve: "CVE explanation",
  explain_vulnerability: "Vulnerability explanation",
  asset_risk: "Asset risk",
  scan_summary: "Scan summary",
  asset_summary: "Asset summary",
  remediation: "Remediation",
  prioritize: "Prioritization",
  executive_summary: "Executive summary",
  technical_summary: "Technical summary",
  dashboard_insights: "Dashboard insights",
  threat_summary: "Threat summary",
  natural_language_search: "Search",
  security_recommendations: "Security recommendations",
  general: "Assistant",
};

interface Props {
  message: ChatMessage;
}

function EntityChip({ message }: Props) {
  const context = message.context;

  if (!context) return null;

  const label = context.cve ?? context.asset_name ?? context.finding_title;

  if (!label) return null;

  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full border border-cyan-800 bg-cyan-950/40 px-2.5 py-0.5 text-[11px] font-semibold text-cyan-300"
      title={context.asset_id ? `Asset id ${context.asset_id}` : undefined}
    >
      <Link2 size={11} />
      {label}
    </span>
  );
}

function ProviderChip({ message }: Props) {
  if (!message.provider || message.provider === "rules") return null;

  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-slate-800 bg-slate-900 px-2.5 py-0.5 text-[11px] font-medium text-slate-400">
      <Cpu size={11} />
      {message.provider}
      {message.model ? ` · ${message.model}` : ""}
    </span>
  );
}

export default function CopilotAnswerMeta({ message }: Props) {
  const intent = message.intent ?? "general";

  return (
    <motion.div
      initial={{ opacity: 0, y: -4 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="mb-2 flex flex-wrap items-center gap-2"
    >
      <span className="inline-flex items-center gap-1.5 rounded-full border border-slate-800 bg-slate-900 px-2.5 py-0.5 text-[11px] font-semibold text-slate-300">
        <Bot size={11} />
        {INTENT_LABELS[intent]}
      </span>
      <EntityChip message={message} />
      <ProviderChip message={message} />
    </motion.div>
  );
}
