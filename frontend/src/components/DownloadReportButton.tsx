import { useState } from "react";
import { Button } from "@/components/ui/button";
import { useAnalysisStore } from "@/store/useAnalysisStore";
import { Download, Loader2 } from "lucide-react";

export default function DownloadReportButton() {
  const downloadReport = useAnalysisStore((s) => s.actions.downloadReport);
  const status = useAnalysisStore((s) => s.status);
  const report = useAnalysisStore((s) => s.report);
  const [downloading, setDownloading] = useState(false);

  if (status !== "ready" || !report) return null;

  const handleClick = async () => {
    setDownloading(true);
    try {
      await downloadReport();
    } finally {
      setDownloading(false);
    }
  };

  return (
    <Button onClick={handleClick} disabled={downloading} className="gap-2">
      {downloading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
      Download PDF Report
    </Button>
  );
}
