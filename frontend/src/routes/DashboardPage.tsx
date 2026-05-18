import { useAnalysisStore } from "@/store/useAnalysisStore";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import RiskScoreGauge from "@/components/RiskScoreGauge";
import RiskHeatmap from "@/components/RiskHeatmap";
import KeyClausesList from "@/components/KeyClausesList";
import SimulationPanel from "@/components/SimulationPanel";
import AgentProgress from "@/components/AgentProgress";
import RecommendationsDiff from "@/components/RecommendationsDiff";
import AuditTrailLog from "@/components/AuditTrailLog";
import DownloadReportButton from "@/components/DownloadReportButton";
import { Navigate } from "react-router-dom";

function SectionSkeleton({ lines = 4 }: { lines?: number }) {
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
  const isAnalyzing = status === "analyzing";

  // Redirect to upload if no job started
  if (status === "idle" && !report) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
      {/* Agent Pipeline Progress (visible during analysis) */}
      <AgentProgress />

      {/* Executive Summary */}
      {report && (
        <div className="bg-muted/40 rounded-lg p-3 sm:p-4 border">
          <h2 className="font-bold text-base sm:text-lg mb-1">{report.headline}</h2>
          <p className="text-sm text-muted-foreground">{report.executive_summary}</p>
        </div>
      )}

      {/* Top row: Risk Score + Heatmap */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
        <Card>
          <CardHeader><CardTitle>Overall Risk Score</CardTitle></CardHeader>
          <CardContent className="flex justify-center">
            {isAnalyzing ? (
              <Skeleton className="h-32 w-48 rounded-full" />
            ) : report ? (
              <RiskScoreGauge score={report.risk_score} />
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Risk Breakdown</CardTitle></CardHeader>
          <CardContent>
            {isAnalyzing ? (
              <SectionSkeleton lines={5} />
            ) : report ? (
              <RiskHeatmap scores={report.per_category_scores} />
            ) : null}
          </CardContent>
        </Card>
      </div>

      {/* Simulation Panel */}
      <Card>
        <CardHeader><CardTitle>What-If Risk Simulation</CardTitle></CardHeader>
        <CardContent>
          {isAnalyzing ? (
            <SectionSkeleton lines={2} />
          ) : report ? (
            <SimulationPanel />
          ) : null}
        </CardContent>
      </Card>

      {/* Key Clauses */}
      <Card>
        <CardHeader><CardTitle>Key Clauses</CardTitle></CardHeader>
        <CardContent>
          {isAnalyzing ? (
            <SectionSkeleton lines={6} />
          ) : report ? (
            <KeyClausesList clauses={report.clauses} analyses={report.clause_analyses} />
          ) : null}
        </CardContent>
      </Card>

      {/* Recommendations */}
      <Card>
        <CardHeader><CardTitle>Recommendations</CardTitle></CardHeader>
        <CardContent>
          {isAnalyzing ? (
            <SectionSkeleton lines={6} />
          ) : report ? (
            <RecommendationsDiff recommendations={report.recommendations} />
          ) : null}
        </CardContent>
      </Card>

      {/* Audit Trail */}
      <Card>
        <CardHeader><CardTitle>Audit Trail</CardTitle></CardHeader>
        <CardContent>
          {isAnalyzing ? (
            <SectionSkeleton lines={4} />
          ) : (
            <AuditTrailLog />
          )}
        </CardContent>
      </Card>

      {/* Footer: Download Report */}
      <div className="flex justify-end pb-4 sm:pb-6">
        <DownloadReportButton />
      </div>
    </div>
  );
}
