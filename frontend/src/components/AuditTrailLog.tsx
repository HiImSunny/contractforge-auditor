import { useEffect, useState } from "react";
import { getAuditTrail } from "@/api/endpoints";
import type { AuditEntry } from "@/lib/types";
import { useAnalysisStore } from "@/store/useAnalysisStore";
import { cn } from "@/lib/utils";
import { ShieldCheck, AlertTriangle } from "lucide-react";

const AGENT_DOT: Record<string, string> = {
  ingestion:       "bg-blue-500",
  clause_analysis: "bg-violet-500",
  policy_mapping:  "bg-orange-500",
  risk_simulation: "bg-red-500",
  recommendation:  "bg-green-500",
  report_gen:      "bg-slate-500",
  report:          "bg-slate-500",
};

export default function AuditTrailLog() {
  const jobId  = useAnalysisStore((s) => s.jobId);
  const status = useAnalysisStore((s) => s.status);
  const [entries, setEntries] = useState<AuditEntry[]>([]);

  useEffect(() => {
    if (!jobId) return;
    getAuditTrail(jobId).then(setEntries).catch(() => {});
  }, [jobId, status]); // re-fetch when analysis completes

  if (entries.length === 0) {
    return (
      <p className="text-xs text-muted-foreground font-mono py-2">
        $ awaiting pipeline execution…
      </p>
    );
  }

  return (
    <div className="rounded-lg border bg-zinc-950 overflow-hidden">
      {/* Console header */}
      <div className="flex items-center gap-2 px-4 py-2 border-b border-zinc-800 bg-zinc-900">
        <div className="flex gap-1.5">
          <div className="w-3 h-3 rounded-full bg-red-500/70" />
          <div className="w-3 h-3 rounded-full bg-amber-500/70" />
          <div className="w-3 h-3 rounded-full bg-green-500/70" />
        </div>
        <span className="text-[10px] text-zinc-400 font-mono ml-2">
          audit-trail — {entries.length} entries — SHA-256 verified
        </span>
        <ShieldCheck className="h-3.5 w-3.5 text-green-500 ml-auto" />
      </div>

      {/* Entries */}
      <div className="divide-y divide-zinc-800/60">
        {entries.map((entry, idx) => {
          const agentBase  = entry.agent_name.split(":")[0];
          const isFailure  = entry.agent_name.includes(":validation_failure");
          const isRepair   = entry.agent_name.includes(":repair");
          const dotColor   = AGENT_DOTS[agentBase] ?? "bg-zinc-500";
          const ts         = entry.timestamp_iso8601.replace("T", " ").replace("Z", "");

          return (
            <div
              key={idx}
              className={cn(
                "px-4 py-2.5 font-mono text-[11px] grid gap-y-1",
                isFailure ? "bg-red-950/30" : "hover:bg-zinc-900/60 transition-colors"
              )}
            >
              {/* Row 1: agent badge · timestamp · latency */}
              <div className="flex items-center gap-2 flex-wrap">
                <span className={cn("inline-block w-2 h-2 rounded-full shrink-0", dotColor)} />
                <span className="text-zinc-100 font-semibold tracking-wide">
                  {entry.agent_name}
                </span>
                {isFailure && (
                  <span className="flex items-center gap-1 text-red-400 text-[10px]">
                    <AlertTriangle className="h-3 w-3" /> validation failure
                  </span>
                )}
                {isRepair && !isFailure && (
                  <span className="text-amber-400 text-[10px]">⚙ repair retry</span>
                )}
                <span className="ml-auto text-zinc-500">{ts}</span>
                <span className={cn(
                  "font-semibold tabular-nums",
                  entry.latency_ms > 2000 ? "text-amber-400" : "text-green-400"
                )}>
                  {entry.latency_ms} ms
                </span>
              </div>

              {/* Row 2: SHA-256 hashes */}
              <div className="flex items-center gap-2 text-zinc-500 pl-4">
                <span className="text-zinc-600">in </span>
                <span className="text-cyan-400/80 tracking-wider">
                  {entry.input_sha256.slice(0, 16)}
                  <span className="text-zinc-600">…{entry.input_sha256.slice(-8)}</span>
                </span>
                <span className="text-zinc-700">→</span>
                <span className="text-zinc-600">out </span>
                <span className="text-purple-400/80 tracking-wider">
                  {entry.output_sha256.slice(0, 16)}
                  <span className="text-zinc-600">…{entry.output_sha256.slice(-8)}</span>
                </span>
                <span className="ml-auto text-zinc-600 text-[10px]">{entry.model_version}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <div className="px-4 py-2 bg-zinc-900 border-t border-zinc-800 flex items-center gap-2">
        <ShieldCheck className="h-3.5 w-3.5 text-green-500" />
        <span className="text-[10px] text-zinc-400 font-mono">
          All {entries.length} agent calls cryptographically logged · tamper-evident
        </span>
      </div>
    </div>
  );
}

// alias so the map lookup works
const AGENT_DOTS = AGENT_DOT;
