import { create } from "zustand";
import type { GovernanceReport, SimulationResult } from "../lib/types";
import * as api from "../api/endpoints";

export type Status = "idle" | "uploading" | "analyzing" | "ready" | "error";

export type AgentName =
  | "ingestion"
  | "clause_analysis"
  | "policy_mapping"
  | "risk_simulation"
  | "recommendation"
  | "report";

export interface AgentProgress {
  current: AgentName | null;
  completed: AgentName[];
}

export interface AnalysisState {
  jobId: string | null;
  status: Status;
  language: "en" | "vi" | null;
  report: GovernanceReport | null;
  agentProgress: AgentProgress;
  error: { code: string; message: string } | null;
  actions: {
    upload: (contract: File, policy: File) => Promise<void>;
    analyze: () => Promise<void>;
    simulate: (key: string) => Promise<SimulationResult>;
    downloadReport: () => Promise<void>;
    loadSample: () => Promise<void>;
    reset: () => void;
  };
}

function toError(e: unknown): { code: string; message: string } {
  if (e && typeof e === "object" && "error_code" in e) {
    return {
      code: (e as { error_code: string }).error_code,
      message:
        "message" in e
          ? String((e as { message: unknown }).message)
          : String(e),
    };
  }
  return { code: "UNKNOWN_ERROR", message: String(e) };
}

export const useAnalysisStore = create<AnalysisState>((set, get) => ({
  jobId: null,
  status: "idle",
  language: null,
  report: null,
  agentProgress: { current: null, completed: [] },
  error: null,

  actions: {
    upload: async (contract, policy) => {
      set({ status: "uploading", error: null });
      try {
        const res = await api.upload(contract, policy);
        set({ jobId: res.job_id, language: res.detected_language, status: "idle" });
      } catch (e) {
        set({ status: "error", error: toError(e) });
      }
    },

    analyze: async () => {
      const id = get().jobId;
      if (!id) return;
      set({ status: "analyzing", agentProgress: { current: "ingestion", completed: [] } });
      try {
        const report = await api.analyzeWithProgress(id, (p) =>
          set({ agentProgress: p })
        );
        set({ report, status: "ready" });
      } catch (e) {
        set({ status: "error", error: toError(e) });
      }
    },

    simulate: async (key) => {
      const id = get().jobId;
      if (!id) throw new Error("No job ID");
      return api.simulate(id, key);
    },

    downloadReport: async () => {
      const id = get().jobId;
      if (!id) return;
      await api.downloadReport(id);
    },

    loadSample: async () => {
      set({ status: "uploading", error: null });
      try {
        const res = await api.loadSample();
        set({ jobId: res.job_id, language: res.detected_language, status: "idle" });
        await get().actions.analyze();
      } catch (e) {
        set({ status: "error", error: toError(e) });
      }
    },

    reset: () =>
      set({
        jobId: null,
        report: null,
        status: "idle",
        error: null,
        language: null,
        agentProgress: { current: null, completed: [] },
      }),
  },
}));
