import { band, BAND_CLASSES, BAND_BAR_CLASSES } from "@/lib/banding";
import type { PerCategoryScores } from "@/lib/types";
import { cn } from "@/lib/utils";

const CATEGORY_LABELS: Record<keyof PerCategoryScores, string> = {
  legal: "Legal",
  financial: "Financial",
  operational: "Operational",
  compliance: "Compliance",
  data_privacy: "Data Privacy",
};

interface Props {
  scores: PerCategoryScores;
}

export default function RiskHeatmap({ scores }: Props) {
  return (
    <div className="space-y-2">
      {(Object.keys(CATEGORY_LABELS) as Array<keyof PerCategoryScores>).map(
        (cat) => {
          const score = scores[cat];
          const b = band(score);
          return (
            <div key={cat} className="flex items-center gap-3">
              <span className="text-sm font-medium w-28 shrink-0">
                {CATEGORY_LABELS[cat]}
              </span>
              <div className="flex-1 bg-gray-100 rounded-full h-3 overflow-hidden">
                <div
                  className={cn(
                    "h-full rounded-full transition-all",
                    BAND_BAR_CLASSES[b]
                  )}
                  style={{ width: `${score}%` }}
                />
              </div>
              <span
                className={cn(
                  "text-xs font-bold w-8 text-right tabular-nums",
                  b === "green"
                    ? "text-green-700"
                    : b === "amber"
                    ? "text-amber-700"
                    : "text-red-700"
                )}
              >
                {score}
              </span>
            </div>
          );
        }
      )}
    </div>
  );
}
