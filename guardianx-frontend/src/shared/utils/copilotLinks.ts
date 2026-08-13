import type { CopilotDeepLink } from "@/types/copilot";

export function findingDeepLink(opts: {
  action: "explain_cve" | "remediation";
  findingId: number;
  cve: string | null;
  title: string;
}): CopilotDeepLink {
  if (opts.action === "explain_cve" && opts.cve) {
    return {
      intent: "explain_cve",
      findingId: opts.findingId,
      cve: opts.cve,
      prompt: `Explain ${opts.cve}.`,
    };
  }

  return {
    intent: "remediation",
    findingId: opts.findingId,
    prompt: `Generate remediation for finding "${opts.title}".`,
  };
}

export function assetDeepLink(assetId: number, assetName: string): CopilotDeepLink {
  return {
    intent: "asset_risk",
    assetId,
    prompt: `Why is the asset "${assetName}" risky?`,
  };
}
