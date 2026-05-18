import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useEffect } from "react";
import { Toaster } from "@/components/ui/toaster";
import Header from "@/components/Header";
import UploadPage from "@/routes/UploadPage";
import DashboardPage from "@/routes/DashboardPage";
import { useAnalysisStore } from "@/store/useAnalysisStore";
import { useToast } from "@/components/ui/use-toast";

function ErrorToastSubscriber() {
  const error = useAnalysisStore((s) => s.error);
  const status = useAnalysisStore((s) => s.status);
  const { toast } = useToast();

  useEffect(() => {
    if (status === "error" && error) {
      toast({
        variant: "destructive",
        title: error.code,
        description: error.message,
      });
    }
  }, [status, error]);

  return null;
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-background text-foreground">
        <Header />
        <ErrorToastSubscriber />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<UploadPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
        <Toaster />
      </div>
    </BrowserRouter>
  );
}
