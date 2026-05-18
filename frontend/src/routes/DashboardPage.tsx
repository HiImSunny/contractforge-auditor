import { useAnalysisStore } from "@/store/useAnalysisStore";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import RiskScoreGauge from "@/components/RiskScoreGauge";
import RiskHeatmap from "@/components/RiskHeatmap";
import SimulationPanel from "@/components/SimulationPanel";
import AgentProgress from "@/components/AgentProgress";
import RecommendationsDiff from "@/components/RecommendationsDiff";
import AuditTrailLog from "@/components/AuditTrailLog";
import DownloadReportButton from "@/components/DownloadReportButton";
import { Navigate } from "react-router-dom";

function Skel({ lines = 4 }: { lines?: number }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton key={i} className="h-4 w-full" />
      ))}
    </div>
  );
}

export default function DashboardPage() {
  const report = useAnalysisStore((s) => s.report);
  const status = useAnalysisStore((s) => s.status);
  const error = useAnalysisStore((s) => s.error);
  const reset = useAnalysisStore((s) => s.actions.reset);
  const isAnalyzing = status === "analyzing";

  if (status === "idle" && !report) return <Navigate to="/" replace />;
  if (status === "error" && error) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 flex flex-col items-center gap-6 text-center">
        <div className="text-5xl">⚠️</div>
        <div>
          <h2 className="text-xl font-bold text-destructive mb-2">Analysis Failed</h2>
          <p className="text-sm text-muted-foreground mb-1">
            <span className="font-mono bg-muted px-1.5 py-0.5 rounded text-xs">{error.code}</span>
          </p>
          <p className="text-sm text-muted-foreground mt-3 max-w-lg">{error.message}</p>
        </div>
        <button
          onClick={reset}
          className="px-4 py-2 rounded-md bg-primary text-primary-foreground text-sm font-medium hover:opacity-90 transition"
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-4 space-y-4">

      {/* ① Agent progress strip — full width horizontal */}
      <AgentProgress />

      {/* Headline when ready */}
      {report && (
        <div className="rounded-lg border bg-muted/30 px-4 py-3">
          <p className="font-semibold text-sm leading-snug">{report.headline}</p>
          <p className="text-xs text-muted-foreground mt-1 leading-relaxed">{report.executive_summary}</p>
        </div>
      )}

      {/* ② Main 2-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_340px] gap-4">

        {/* LEFT — Redline Diff */}
        <Card className="min-h-[420px]">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">
              Side-by-side Redline Diff
              <span className="text-muted-foreground font-normal ml-1">(Original vs. Proposed Clause)</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isAnalyzing ? <Skel lines={8} /> : report ? (
              <RecommendationsDiff recommendations={report.recommendations} />
            ) : null}
          </CardContent>
        </Card>

        {/* RIGHT — Gauge + Heatmap + Download */}
        <div className="flex flex-col gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Risk Score Gauge (0-100)</CardTitle>
            </CardHeader>
            <CardContent className="flex justify-center pb-3">
              {isAnalyzing ? (
                <Skeleton className="h-28 w-44 rounded-full" />
              ) : report ? (
                <RiskScoreGauge score={report.risk_score} />
              ) : null}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Per-category Risk Heatmap</CardTitle>
            </CardHeader>
            <CardContent>
              {isAnalyzing ? <Skel lines={5} /> : report ? (
                <RiskHeatmap scores={report.per_category_scores} />
              ) : null}
            </CardContent>
          </Card>

          {/* Download button — prominent, right column */}
          <DownloadReportButton className="w-full h-12 text-sm font-semibold" />
        </div>
      </div>

      {/* ③ What-If Simulation Panel — full width */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">
            What-If Simulation Panel
            <span className="text-muted-foreground font-normal ml-1">(Click a scenario → Instant impact score)</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isAnalyzing ? <Skel lines={2} /> : report ? <SimulationPanel /> : null}
        </CardContent>
      </Card>

      {/* ④ Audit Trail — console style */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">
            Cryptographic Audit Trail
            <span className="text-muted-foreground font-normal ml-1">(SHA-256 hashes, timestamps, latency per agent)</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isAnalyzing ? <Skel lines={4} /> : <AuditTrailLog />}
        </CardContent>
      </Card>

    </div>
  );
}
