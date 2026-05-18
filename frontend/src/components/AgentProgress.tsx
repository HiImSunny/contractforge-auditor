import { useAnalysisStore } from "@/store/useAnalysisStore";
import type { AgentName } from "@/store/useAnalysisStore";
import { cn } from "@/lib/utils";
import { CheckCircle2, Circle, Loader2 } from "lucide-react";

const AGENT_LABELS: Record<AgentName, string> = {
  ingestion: "Ingestion & Extraction",
  clause_analysis: "Clause Analysis",
  policy_mapping: "Policy Compliance",
  risk_simulation: "Risk Simulation",
  recommendation: "Recommendations",
  report: "Report Generation",
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

  if (status !== "analyzing") return null;

  return (
    <div className="border rounded-lg p-4 bg-muted/20">
      <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-3">
        Agent Pipeline
      </p>
      <div className="space-y-2">
        {AGENT_ORDER.map((agent) => {
          const isDone = completed.includes(agent);
          const isRunning = current === agent;
          return (
            <div
              key={agent}
              className={cn(
                "flex items-center gap-2 text-sm",
                isDone ? "text-foreground" : "text-muted-foreground"
              )}
            >
              {isDone ? (
                <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0" />
              ) : isRunning ? (
                <Loader2 className="h-4 w-4 animate-spin text-primary shrink-0" />
              ) : (
                <Circle className="h-4 w-4 shrink-0" />
              )}
              <span className={cn(isRunning && "font-semibold text-primary")}>
                {AGENT_LABELS[agent]}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
