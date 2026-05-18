import { useState } from "react";
import { Button } from "@/components/ui/button";
import { useAnalysisStore } from "@/store/useAnalysisStore";
import { Download, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface Props {
  className?: string;
}

export default function DownloadReportButton({ className }: Props) {
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
    <Button onClick={handleClick} disabled={downloading} className={cn("gap-2", className)}>
      {downloading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
      Download PDF Governance Report
    </Button>
  );
}
