import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useAnalysisStore } from "@/store/useAnalysisStore";
import type { SimulationResult, ScenarioKey } from "@/lib/types";
import { band, BAND_CLASSES } from "@/lib/banding";
import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

const SCENARIOS: { key: ScenarioKey; label: string; icon: string }[] = [
  { key: "force_majeure", label: "Force Majeure", icon: "🌪️" },
  { key: "penalty_delay", label: "Penalty Delay", icon: "⏰" },
  { key: "data_breach", label: "Data Breach", icon: "🔓" },
  { key: "termination", label: "Termination", icon: "🚫" },
  { key: "payment_default", label: "Payment Default", icon: "💸" },
];

export default function SimulationPanel() {
  const simulate = useAnalysisStore((s) => s.actions.simulate);
  const report = useAnalysisStore((s) => s.report);
  const [results, setResults] = useState<Record<string, SimulationResult>>({});
  const [loading, setLoading] = useState<string | null>(null);
  const [active, setActive] = useState<string | null>(null);

  // Pre-populate from report if available
  const getResult = (key: string): SimulationResult | undefined => {
    if (results[key]) return results[key];
    return report?.simulations.find((s) => s.scenario_key === key);
  };

  const handleSimulate = async (key: ScenarioKey) => {
    setLoading(key);
    setActive(key);
    try {
      const result = await simulate(key);
      setResults((prev) => ({ ...prev, [key]: result }));
    } catch {
      // error handled by store
    }
    setLoading(null);
  };

  const activeResult = active ? getResult(active) : null;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {SCENARIOS.map(({ key, label, icon }) => (
          <Button
            key={key}
            variant={active === key ? "default" : "outline"}
            size="sm"
            onClick={() => handleSimulate(key)}
            disabled={loading !== null}
            className="gap-1"
          >
            {loading === key ? (
              <Loader2 className="h-3 w-3 animate-spin" />
            ) : (
              <span>{icon}</span>
            )}
            {label}
          </Button>
        ))}
      </div>

      {activeResult && (
        <div className="border rounded-lg p-4 space-y-3 bg-muted/30">
          <div className="flex items-center justify-between">
            <span className="font-semibold text-sm">
              {SCENARIOS.find((s) => s.key === active)?.label}
            </span>
            <span
              className={cn(
                "text-sm font-bold px-2 py-0.5 rounded border",
                BAND_CLASSES[band(activeResult.impact_score)]
              )}
            >
              Impact: {activeResult.impact_score}/100
            </span>
          </div>
          <p className="text-sm text-muted-foreground">{activeResult.narrative}</p>
          {activeResult.affected_clause_ids?.length > 0 && (
            <div className="flex flex-wrap gap-1">
              <span className="text-xs text-muted-foreground">Affected:</span>
              {activeResult.affected_clause_ids.map((id) => (
                <Badge key={id} variant="outline" className="text-xs">
                  {id}
                </Badge>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
