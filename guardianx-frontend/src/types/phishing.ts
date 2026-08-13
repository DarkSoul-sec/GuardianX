export type PhishingRiskLevel = "low" | "medium" | "high" | "critical";

export interface PhishingCheckResult {
  check: string;
  title: string;
  score: number;
  severity: string;
  reason: string;
  recommendation: string;
  data: Record<string, unknown>;
}

export interface PhishingAnalysisResponse {
  url: string;
  threat_score: number;
  risk_level: PhishingRiskLevel;
  reasons: string[];
  recommendations: string[];
  ai_summary: string;
  checks: PhishingCheckResult[];
  generated_at: string;
}
