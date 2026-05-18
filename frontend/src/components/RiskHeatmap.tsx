import type { PerCategoryScores } from "@/lib/types";
import { cn } from "@/lib/utils";

const CATEGORY_LABELS: Record<keyof PerCategoryScores, string> = {
  legal: "Legal",
  financial: "Financial",
  operational: "Operational",
  compliance: "Compliance",
  data_privacy: "Data Privacy",
};

// 10 cells per row, each cell = 10 points
const CELLS = 10;

function cellColor(cellIndex: number, score: number): string {
  const threshold = cellIndex * 10; // cell i lights up when score > i*10
  if (score <= threshold) return "bg-muted/40 border border-border";

  // Color based on which zone the score falls in
  if (score <= 33) return "bg-green-500";
  if (score <= 66) return "bg-amber-500";
  // red zone — gradient: lighter red for early cells, deeper for later
  const intensity = cellIndex >= 7 ? "bg-red-600" : cellIndex >= 5 ? "bg-red-500" : "bg-red-400";
  return intensity;
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
        const scoreColor =
          score <= 33 ? "text-green-600" : score <= 66 ? "text-amber-600" : "text-red-600";

        return (
          <div key={cat} className="flex items-center gap-2">
            {/* Label */}
            <span className="text-xs font-medium w-24 shrink-0 truncate">
              {CATEGORY_LABELS[cat]}
            </span>

            {/* Heat cells */}
            <div className="flex-1 flex gap-0.5">
              {Array.from({ length: CELLS }).map((_, i) => (
                <div
                  key={i}
                  className={cn(
                    "flex-1 h-5 rounded-sm transition-colors",
                    cellColor(i, score)
                  )}
                  title={`${(i + 1) * 10}`}
                />
              ))}
            </div>

            {/* Score */}
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
