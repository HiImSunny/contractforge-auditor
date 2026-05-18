import { useAnalysisStore } from "@/store/useAnalysisStore";
import type { AgentName } from "@/store/useAnalysisStore";
import { cn } from "@/lib/utils";
import { CheckCircle2, Circle, Loader2 } from "lucide-react";

const AGENT_LABELS: Record<AgentName, string> = {
  ingestion: "Ingestion",
  clause_analysis: "Clause Analysis",
  policy_mapping: "Policy Mapping",
  risk_simulation: "Risk Simulation",
  recommendation: "Recommendations",
  report: "Report Gen",
};

const AGENT_ORDER: AgentName[] = [
  "ingestion",
  "clause_analysis",
  "policy_mapping",
  "risk_simulation",
  "recommendation",
  "report",
];

export default function AgentProgress() {
  const { current, completed } = useAnalysisStore((s) => s.agentProgress);
  const status = useAnalysisStore((s) => s.status);

  // Show during analysis AND after completion (all green)
  if (status !== "analyzing" && status !== "ready") return null;

  const allDone = status === "ready";

  return (
    <div className="w-full border rounded-lg px-4 py-3 bg-muted/20">
      <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-widest mb-3">
        Real-time agent progress strip (6 LangGraph steps)
      </p>
      <div className="flex items-center gap-0">
        {AGENT_ORDER.map((agent, idx) => {
          const isDone = allDone || completed.includes(agent);
          const isRunning = !allDone && current === agent;

          return (
            <div key={agent} className="flex items-center flex-1 min-w-0">
              {/* Node */}
              <div className="flex flex-col items-center gap-1 flex-1 min-w-0">
                <div
                  className={cn(
                    "w-7 h-7 rounded-full flex items-center justify-center border-2 shrink-0 transition-all",
                    isDone
                      ? "bg-green-500 border-green-500 text-white"
                      : isRunning
                      ? "bg-primary border-primary text-white"
                      : "bg-background border-muted-foreground/30 text-muted-foreground"
                  )}
                >
                  {isDone ? (
                    <CheckCircle2 className="h-4 w-4" />
                  ) : isRunning ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Circle className="h-3.5 w-3.5" />
                  )}
                </div>
                <span
                  className={cn(
                    "text-[9px] font-medium text-center leading-tight truncate w-full px-0.5",
                    isDone
                      ? "text-green-600"
                      : isRunning
                      ? "text-primary font-bold"
                      : "text-muted-foreground"
                  )}
                >
                  {AGENT_LABELS[agent]}
                </span>
              </div>
              {/* Connector line */}
              {idx < AGENT_ORDER.length - 1 && (
                <div
                  className={cn(
                    "h-0.5 w-full max-w-[32px] shrink-0 rounded transition-all",
                    allDone || completed.includes(AGENT_ORDER[idx + 1])
                      ? "bg-green-400"
                      : isDone
                      ? "bg-green-400"
                      : isRunning
                      ? "bg-primary/40"
                      : "bg-muted-foreground/20"
                  )}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
