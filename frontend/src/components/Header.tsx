import { Shield } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { useAnalysisStore } from "@/store/useAnalysisStore";

export default function Header() {
  const reset = useAnalysisStore((s) => s.actions.reset);
  const status = useAnalysisStore((s) => s.status);

  return (
    <header className="border-b bg-card shadow-sm">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 font-bold text-xl text-primary">
          <Shield className="h-6 w-6" />
          ContractForge Auditor
        </Link>
        <div className="flex items-center gap-3">
          <span className="text-xs text-muted-foreground hidden sm:block">
            AI Contract Governance
          </span>
          {status !== "idle" && (
            <Button variant="ghost" size="sm" onClick={reset}>
              New Analysis
            </Button>
          )}
        </div>
      </div>
    </header>
  );
}
