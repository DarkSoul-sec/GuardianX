export type CopilotIntent =
  | "explain_cve"
  | "explain_vulnerability"
  | "asset_risk"
  | "scan_summary"
  | "asset_summary"
  | "remediation"
  | "prioritize"
  | "executive_summary"
  | "technical_summary"
  | "dashboard_insights"
  | "threat_summary"
  | "natural_language_search"
  | "security_recommendations"
  | "general";

export interface CopilotChatRequest {
  message: string;
  type?: CopilotIntent;
  asset_id?: number;
  finding_id?: number;
  cve?: string;
}

export interface CopilotResolvedContext {
  cve?: string | null;
  asset_id?: number | null;
  asset_name?: string | null;
  finding_id?: number | null;
  finding_title?: string | null;
}

export interface CopilotResultItem {
  kind: "finding" | "asset" | "service" | "cve";
  id?: number | null;
  title: string;
  detail?: string | null;
  severity?: string | null;
  status?: string | null;
  score?: string | null;
}

export interface CopilotChatResponse {
  answer: string;
  intent: CopilotIntent;
  provider: string;
  model?: string | null;
  context?: CopilotResolvedContext | null;
  results?: CopilotResultItem[] | null;
}

export interface CopilotProviderInfo {
  provider: string;
  model?: string | null;
  built_in: boolean;
  available: string[];
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  intent?: CopilotIntent;
  provider?: string;
  model?: string | null;
  context?: CopilotResolvedContext | null;
  results?: CopilotResultItem[] | null;
  error?: boolean;
  /** True while a streamed answer is still being appended. */
  streaming?: boolean;
}

/** Context carried from other pages when deep-linking into the Copilot. */
export interface CopilotDeepLink {
  intent: CopilotIntent;
  prompt: string;
  assetId?: number;
  assetName?: string;
  findingId?: number;
  findingTitle?: string;
  cve?: string;
}

export interface CopilotMemoryStatus {
  turns: number;
  ttl_seconds: number;
}

export interface CopilotMemoryClearResponse {
  cleared: number;
}

/** Streamed SSE event payloads from POST /copilot/chat/stream. */
export interface CopilotStreamMeta {
  type: "meta";
  intent: CopilotIntent;
  provider: string;
  model?: string | null;
  context?: CopilotResolvedContext | null;
}

export interface CopilotStreamToken {
  type: "token";
  content: string;
}

export interface CopilotStreamDone {
  type: "done";
  content: string;
  context?: CopilotResolvedContext | null;
  results?: CopilotResultItem[] | null;
}

export interface CopilotStreamError {
  type: "error";
  message: string;
}

export type CopilotStreamEvent =
  | CopilotStreamMeta
  | CopilotStreamToken
  | CopilotStreamDone
  | CopilotStreamError;
