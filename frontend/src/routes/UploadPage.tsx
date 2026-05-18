import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { UploadDropzone } from "@/components/UploadDropzone";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { useAnalysisStore } from "@/store/useAnalysisStore";
import { Loader2 } from "lucide-react";

export default function UploadPage() {
  const [contract, setContract] = useState<File | null>(null);
  const [policy, setPolicy] = useState<File | null>(null);
  const navigate = useNavigate();
  const { upload, analyze, loadSample } = useAnalysisStore((s) => s.actions);
  const status = useAnalysisStore((s) => s.status);
  const isLoading = status === "uploading" || status === "analyzing";

  const handleSubmit = async () => {
    if (!contract || !policy) return;
    await upload(contract, policy);
    await analyze();
    navigate("/dashboard");
  };

  const handleLoadSample = async () => {
    await loadSample();
    navigate("/dashboard");
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold mb-2">Contract Governance Audit</h1>
        <p className="text-muted-foreground">
          Upload a contract and policy file to run a multi-agent AI analysis.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Upload Files</CardTitle>
          <CardDescription>
            Contract: PDF or TXT · Policy: PDF, CSV, or TXT · Max 15 MB each
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <UploadDropzone
            label="Contract Document"
            accept=".pdf,.txt"
            file={contract}
            onFile={setContract}
            onClear={() => setContract(null)}
          />
          <UploadDropzone
            label="Policy Document"
            accept=".pdf,.csv,.txt"
            file={policy}
            onFile={setPolicy}
            onClear={() => setPolicy(null)}
          />
          <div className="flex gap-3 pt-2">
            <Button
              className="flex-1"
              disabled={!contract || !policy || isLoading}
              onClick={handleSubmit}
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Analyzing...
                </>
              ) : (
                "Analyze Contract"
              )}
            </Button>
            <Button variant="outline" disabled={isLoading} onClick={handleLoadSample}>
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                "Load Sample"
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
