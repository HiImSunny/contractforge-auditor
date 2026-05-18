import { useEffect, useState } from "react";
import { getAuditTrail } from "@/api/endpoints";
import type { AuditEntry } from "@/lib/types";
import { useAnalysisStore } from "@/store/useAnalysisStore";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const AGENT_COLORS: Record<string, string> = {
  ingestion: "bg-blue-100 text-blue-800",
  clause_analysis: "bg-purple-100 text-purple-800",
  policy_mapping: "bg-orange-100 text-orange-800",
  risk_simulation: "bg-red-100 text-red-800",
  recommendation: "bg-green-100 text-green-800",
  report: "bg-gray-100 text-gray-800",
};

export default function AuditTrailLog() {
  const jobId = useAnalysisStore((s) => s.jobId);
  const [entries, setEntries] = useState<AuditEntry[]>([]);

  useEffect(() => {
    if (!jobId) return;
    getAuditTrail(jobId).then(setEntries).catch(() => {});
  }, [jobId]);

  if (entries.length === 0) {
    return <p className="text-sm text-muted-foreground">No audit entries yet.</p>;
  }

  return (
    <div className="space-y-2">
      {entries.map((entry, idx) => {
        const agentBase = entry.agent_name.split(":")[0];
        const isFailure = entry.agent_name.includes(":validation_failure");
        return (
          <div key={idx} className="border rounded-lg p-3 text-xs font-mono space-y-1">
            <div className="flex items-center justify-between gap-2 flex-wrap">
              <span
                className={cn(
                  "px-2 py-0.5 rounded text-xs font-semibold",
                  AGENT_COLORS[agentBase] ?? "bg-gray-100 text-gray-800"
                )}
              >
                {entry.agent_name}
              </span>
              {isFailure && (
                <Badge variant="destructive" className="text-xs">
                  validation failure
                </Badge>
              )}
              <span className="text-muted-foreground ml-auto">{entry.latency_ms}ms</span>
            </div>
            <div className="text-muted-foreground">
              <span className="text-foreground/60">{entry.timestamp_iso8601}</span>
              {" · "}
              <span>{entry.model_version}</span>
            </div>
            <div className="text-muted-foreground/70 truncate">
              in: {entry.input_sha256.slice(0, 8)}… · out: {entry.output_sha256.slice(0, 8)}…
            </div>
          </div>
        );
      })}
    </div>
  );
}
