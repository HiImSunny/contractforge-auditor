import type { Clause, ClauseAnalysis } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface Props {
  clauses: Clause[];
  analyses: ClauseAnalysis[];
}

export default function KeyClausesList({ clauses, analyses }: Props) {
  const analysisMap = new Map(analyses.map((a) => [a.clause_id, a]));

  return (
    <div className="space-y-3">
      {clauses.map((clause) => {
        const analysis = analysisMap.get(clause.clause_id);
        return (
          <div
            key={clause.clause_id}
            className="border rounded-lg p-4 space-y-1"
          >
            <div className="flex items-start justify-between gap-2">
              <span className="text-sm font-semibold text-foreground">
                {clause.heading ?? clause.clause_id}
              </span>
              {analysis && (
                <Badge variant="secondary" className="text-xs shrink-0">
                  {analysis.clause_type.replace(/_/g, " ")}
                </Badge>
              )}
            </div>
            {analysis && (
              <p className="text-sm text-muted-foreground leading-relaxed">
                {analysis.summary}
              </p>
            )}
          </div>
        );
      })}
    </div>
  );
}
