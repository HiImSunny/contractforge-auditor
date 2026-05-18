import type { PerCategoryScores } from "@/lib/types";
import { cn } from "@/lib/utils";

const CATEGORY_LABELS: Record<keyof PerCategoryScores, string> = {
  legal: "Legal",
  financial: "Financial",
  operational: "Operational",
  compliance: "Compliance",
  data_privacy: "Data Privacy",
};

const CELLS = 10; // each cell = 10 points

// All filled cells get the same color based on the category's score band
function filledColor(score: number): string {
  if (score <= 33) return "bg-green-500";
  if (score <= 66) return "bg-amber-500";
  return "bg-red-500";
}

interface Props {
  scores: PerCategoryScores;
}

export default function RiskHeatmap({ scores }: Props) {
  if (!scores) return null;

  return (
    <div className="space-y-2.5">
      {/* Column headers */}
      <div className="flex items-center gap-2 mb-1">
        <span className="w-24 shrink-0" />
        <div className="flex-1 flex justify-between px-0.5">
          <span className="text-[9px] text-muted-foreground">0</span>
          <span className="text-[9px] text-muted-foreground">50</span>
          <span className="text-[9px] text-muted-foreground">100</span>
        </div>
        <span className="w-8 shrink-0" />
      </div>

      {(Object.keys(CATEGORY_LABELS) as Array<keyof PerCategoryScores>).map((cat) => {
        const score = scores[cat] ?? 0;
        // How many cells to fill: score=30 → 3 cells, score=80 → 8 cells
        const filledCells = Math.round(score / 10);
        const color = filledColor(score);
        const scoreColor =
          score <= 33 ? "text-green-600" : score <= 66 ? "text-amber-600" : "text-red-600";

        return (
          <div key={cat} className="flex items-center gap-2">
            <span className="text-xs font-medium w-24 shrink-0 truncate">
              {CATEGORY_LABELS[cat]}
            </span>

            <div className="flex-1 flex gap-0.5">
              {Array.from({ length: CELLS }).map((_, i) => (
                <div
                  key={i}
                  className={cn(
                    "flex-1 h-5 rounded-sm transition-colors",
                    i < filledCells ? color : "bg-muted/40 border border-border"
                  )}
                />
              ))}
            </div>

            <span className={cn("text-xs font-bold w-8 text-right tabular-nums", scoreColor)}>
              {score}
            </span>
          </div>
        );
      })}

      {/* Legend */}
      <div className="flex items-center gap-3 pt-1 border-t mt-1">
        <span className="text-[9px] text-muted-foreground">Risk level:</span>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-sm bg-green-500" />
          <span className="text-[9px] text-muted-foreground">Low (0–33)</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-sm bg-amber-500" />
          <span className="text-[9px] text-muted-foreground">Medium (34–66)</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-sm bg-red-500" />
          <span className="text-[9px] text-muted-foreground">High (67–100)</span>
        </div>
      </div>
    </div>
  );
}
