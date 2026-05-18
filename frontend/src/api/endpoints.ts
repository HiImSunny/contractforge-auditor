// frontend/src/api/endpoints.ts
import { apiFetch, apiFetchBlob } from "./client";
import type {
  GovernanceReport,
  SimulationResult,
  AuditEntry,
  UploadResponse,
} from "../lib/types";
import type { AgentProgress, AgentName } from "../store/useAnalysisStore";

const AGENT_ORDER: AgentName[] = [
  "ingestion",
  "clause_analysis",
  "policy_mapping",
  "risk_simulation",
  "recommendation",
  "report",
];

export async function upload(contract: File, policy: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append("contract", contract);
  form.append("policy", policy);
  return apiFetch<UploadResponse>("/api/upload", {
    method: "POST",
    headers: {},  // let browser set multipart boundary
    body: form,
  });
}

export async function analyze(jobId: string): Promise<GovernanceReport> {
  return apiFetch<GovernanceReport>("/api/analyze", {
    method: "POST",
    body: JSON.stringify({ job_id: jobId }),
  });
}

export async function analyzeWithProgress(
  jobId: string,
  onProgress: (p: AgentProgress) => void
): Promise<GovernanceReport> {
  // Start the analysis (long-running)
  const analyzePromise = analyze(jobId);

  // Poll audit trail every 1.5s to infer agent progress
  const interval = setInterval(async () => {
    try {
      const entries = await getAuditTrail(jobId);
      const completedAgents = entries
        .map((e) => e.agent_name as AgentName)
        .filter((name) => AGENT_ORDER.includes(name));

      const newCompleted = [...new Set(completedAgents)];
      const nextIdx = newCompleted.length;
      const current = nextIdx < AGENT_ORDER.length ? AGENT_ORDER[nextIdx] : null;

      onProgress({ current, completed: newCompleted });
    } catch {}
  }, 1500);

  try {
    const report = await analyzePromise;
    clearInterval(interval);
    onProgress({ current: null, completed: [...AGENT_ORDER] });
    return report;
  } catch (e) {
    clearInterval(interval);
    throw e;
  }
}

export async function simulate(jobId: string, scenarioKey: string): Promise<SimulationResult> {
  return apiFetch<SimulationResult>("/api/simulate", {
    method: "POST",
    body: JSON.stringify({ job_id: jobId, scenario_key: scenarioKey }),
  });
}

export async function downloadReport(jobId: string): Promise<void> {
  const blob = await apiFetchBlob(`/api/report/${jobId}`);
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `contractforge-report-${jobId}.pdf`;
  a.click();
  URL.revokeObjectURL(url);
}

export async function loadSample(): Promise<{ job_id: string; detected_language: "en" | "vi" }> {
  return apiFetch("/api/load-sample", { method: "POST" });
}

export async function getAuditTrail(jobId: string): Promise<AuditEntry[]> {
  return apiFetch<AuditEntry[]>(`/api/audit-trail/${jobId}`);
}

export async function getHealth(): Promise<{ status: string; version: string; gemini_configured: boolean }> {
  return apiFetch("/api/health");
}
