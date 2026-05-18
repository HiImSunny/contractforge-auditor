// frontend/src/lib/types.ts
// TypeScript types mirroring the backend Pydantic schemas (Req 8)

export type Language = "en" | "vi";

export type RiskCategory = "legal" | "financial" | "operational" | "compliance" | "data_privacy";

export type Severity = "low" | "medium" | "high" | "critical";

export type ScenarioKey = "force_majeure" | "penalty_delay" | "data_breach" | "termination" | "payment_default";

export type ClauseType =
  | "term" | "termination" | "payment" | "confidentiality" | "data_protection"
  | "liability" | "indemnification" | "force_majeure" | "governing_law"
  | "ip_assignment" | "warranty" | "service_level" | "compliance" | "other";

export interface CharSpan {
  start: number;
  end: number;
}

export interface Clause {
  clause_id: string;
  heading: string | null;
  text: string;
  language: Language;
  char_span: CharSpan;
}

export interface ClauseAnalysis {
  clause_id: string;
  clause_type: ClauseType;
  summary: string;
  key_terms: string[];
}

export interface Violation {
  clause_id: string;
  policy_rule_id: string;
  risk_category: RiskCategory;
  severity: Severity;
  rationale: string;
}

export interface SimulationResult {
  scenario_key: ScenarioKey;
  impact_score: number;
  affected_clause_ids: string[];
  narrative: string;
}

export interface Recommendation {
  clause_id: string;
  original_text: string;
  proposed_text: string;
  change_rationale: string;
}

export interface PerCategoryScores {
  legal: number;
  financial: number;
  operational: number;
  compliance: number;
  data_privacy: number;
}

export interface GovernanceReport {
  job_id: string;
  language: Language;
  headline: string;
  executive_summary: string;
  top_risks: string[];
  risk_score: number;
  per_category_scores: PerCategoryScores;
  clauses: Clause[];
  clause_analyses: ClauseAnalysis[];
  violations: Violation[];
  simulations: SimulationResult[];
  recommendations: Recommendation[];
  audit_trail: AuditEntry[];
}

export interface AuditEntry {
  job_id: string;
  agent_name: string;
  input_sha256: string;
  output_sha256: string;
  timestamp_iso8601: string;
  model_version: string;
  latency_ms: number;
}

export interface UploadResponse {
  job_id: string;
  contract_filename: string;
  policy_filename: string;
  detected_language: Language;
}

export interface ApiError {
  error_code: string;
  message: string;
  [key: string]: unknown;
}
