import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { useAnalysisStore } from "@/store/useAnalysisStore";
import { FlaskConical, Loader2 } from "lucide-react";

export default function LoadSampleButton() {
  const loadSample = useAnalysisStore((s) => s.actions.loadSample);
  const status = useAnalysisStore((s) => s.status);
  const navigate = useNavigate();
  const isLoading = status === "uploading" || status === "analyzing";

  const handleClick = async () => {
    await loadSample();
    navigate("/dashboard");
  };

  return (
    <Button variant="outline" onClick={handleClick} disabled={isLoading} className="gap-2">
      {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <FlaskConical className="h-4 w-4" />}
      Load Sample Data
    </Button>
  );
}
