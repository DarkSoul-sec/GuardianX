import {
  FileSearch,
  FileText,
  LayoutDashboard,
  Layers,
  ListOrdered,
  ScanSearch,
  Search,
  Server,
  ShieldAlert,
  ShieldCheck,
  Swords,
  Wrench,
} from "lucide-react";

import type { CopilotIntent } from "@/types/copilot";

export interface CopilotAction {
  intent: CopilotIntent;
  label: string;
  prompt: string;
  icon: typeof Server;
}

export const COPILOT_ACTIONS: CopilotAction[] = [
  {
    intent: "explain_cve",
    label: "Explain a CVE",
    prompt: "Explain this CVE: CVE-2021-44228",
    icon: FileSearch,
  },
  {
    intent: "explain_vulnerability",
    label: "Explain a vulnerability",
    prompt: "Explain the most critical vulnerability in my estate.",
    icon: ShieldAlert,
  },
  {
    intent: "asset_risk",
    label: "Why is this asset risky?",
    prompt: "Why is this asset risky? ",
    icon: Server,
  },
  {
    intent: "scan_summary",
    label: "Summarize today's scans",
    prompt: "Summarize today's scans.",
    icon: ScanSearch,
  },
  {
    intent: "asset_summary",
    label: "Summarize assets",
    prompt: "Summarize the assets in my estate.",
    icon: Layers,
  },
  {
    intent: "natural_language_search",
    label: "Show critical vulns",
    prompt: "Show my critical vulnerabilities.",
    icon: Search,
  },
  {
    intent: "technical_summary",
    label: "Technical summary",
    prompt: "Generate a technical security summary for my estate.",
    icon: FileText,
  },
  {
    intent: "dashboard_insights",
    label: "Dashboard insights",
    prompt: "Show me dashboard insights for my estate.",
    icon: LayoutDashboard,
  },
  {
    intent: "threat_summary",
    label: "Threat summary",
    prompt: "Give me a full threat summary for CVE-2021-44228 combining all sources.",
    icon: Swords,
  },
  {
    intent: "remediation",
    label: "Generate remediation",
    prompt: "Generate remediation for the most critical finding.",
    icon: Wrench,
  },
  {
    intent: "prioritize",
    label: "Prioritize vulnerabilities",
    prompt: "Prioritize vulnerabilities.",
    icon: ListOrdered,
  },
  {
    intent: "executive_summary",
    label: "Executive summary",
    prompt: "Generate executive summary.",
    icon: FileText,
  },
  {
    intent: "security_recommendations",
    label: "Security recommendations",
    prompt: "Give me security recommendations for my estate.",
    icon: ShieldCheck,
  },
];
