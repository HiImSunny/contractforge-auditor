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

export async function analyze(jobId: string): Promise<{ status: string; job_id: string }> {
  return apiFetch("/api/analyze", {
    method: "POST",
    body: JSON.stringify({ job_id: jobId }),
  });
}

export async function analyzeWithProgress(
  jobId: string,
  onProgress: (p: AgentProgress) => void
): Promise<GovernanceReport> {
  // Kick off the pipeline
  await analyze(jobId);

  return new Promise((resolve, reject) => {
    const completed: AgentName[] = [];
    const apiBase = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");
    const es = new EventSource(`${apiBase}/api/analyze/stream/${jobId}`);

    es.addEventListener("agent_start", (e) => {
      const { agent } = JSON.parse(e.data) as { agent: AgentName };
      if (AGENT_ORDER.includes(agent)) {
        onProgress({ current: agent, completed: [...completed] });
      }
    });

    es.addEventListener("agent_done", (e) => {
      const { agent } = JSON.parse(e.data) as { agent: AgentName };
      if (AGENT_ORDER.includes(agent) && !completed.includes(agent)) {
        completed.push(agent);
        const nextIdx = completed.length;
        const current = nextIdx < AGENT_ORDER.length ? AGENT_ORDER[nextIdx] : null;
        onProgress({ current, completed: [...completed] });
      }
    });

    es.addEventListener("done", () => {
      es.close();
      onProgress({ current: null, completed: [...AGENT_ORDER] });
      // Fetch the completed report
      apiFetch<{ status: string; report?: GovernanceReport }>(
        `/api/analyze/status/${jobId}`
      ).then((res) => {
        if (res.report) resolve(res.report);
        else reject({ error_code: "EMPTY_REPORT", message: "Pipeline done but report missing" });
      }).catch(reject);
    });

    es.addEventListener("error", (e) => {
      es.close();
      try {
        const err = JSON.parse((e as MessageEvent).data ?? "{}");
        reject(err);
      } catch {
        reject({ error_code: "STREAM_ERROR", message: "SSE connection error" });
      }
    });

    // Fallback: if SSE not supported or connection drops, poll
    es.onerror = () => {
      if (es.readyState === EventSource.CLOSED) {
        // Already handled by "done"/"error" events — ignore
      }
    };
  });
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
