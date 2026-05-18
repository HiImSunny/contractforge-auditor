import type { Recommendation } from "@/lib/types";
import { wordDiff, type DiffToken } from "@/lib/diff";
import { cn } from "@/lib/utils";

function DiffText({ tokens }: { tokens: DiffToken[] }) {
  return (
    <p className="text-sm leading-relaxed font-mono whitespace-pre-wrap">
      {tokens.map((t, i) => (
        <span
          key={i}
          className={cn(
            t.type === "added" && "bg-green-100 text-green-800",
            t.type === "removed" && "bg-red-100 text-red-800 line-through"
          )}
        >
          {t.text}
        </span>
      ))}
    </p>
  );
}

interface Props {
  recommendations: Recommendation[];
}

export default function RecommendationsDiff({ recommendations }: Props) {
  if (!recommendations || recommendations.length === 0) {
    return <p className="text-sm text-muted-foreground">No recommendations.</p>;
  }

  return (
    <div className="space-y-6">
      {recommendations.map((rec, idx) => {
        const { original, proposed } = wordDiff(rec.original_text, rec.proposed_text);
        return (
          <div key={`${rec.clause_id}-${idx}`} className="border rounded-lg overflow-hidden">
            <div className="bg-muted/40 px-4 py-2 border-b">
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                {rec.clause_id}
              </span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x">
              <div className="p-4">
                <p className="text-xs font-semibold text-red-600 mb-2 uppercase tracking-wide">Original</p>
                <DiffText tokens={original} />
              </div>
              <div className="p-4">
                <p className="text-xs font-semibold text-green-600 mb-2 uppercase tracking-wide">Proposed</p>
                <DiffText tokens={proposed} />
              </div>
            </div>
            <div className="bg-muted/20 px-4 py-2 border-t">
              <p className="text-xs text-muted-foreground">
                <span className="font-semibold">Rationale:</span> {rec.change_rationale}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
