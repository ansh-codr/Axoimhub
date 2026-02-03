// =============================================================================
// Axiom Design Engine - Generate 3D Page
// Direct 3D model generation page
// =============================================================================

"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useJobsStore, useToast } from "@/store";
import { PromptEditor } from "@/components/generation/prompt-editor";
import { JobsList } from "@/components/generation/job-status-panel";
import type { GenerationRequest } from "@/types";

export default function Generate3DPage() {
  const router = useRouter();
  const { toast } = useToast();
  const { jobs, createJob, cancelJob, retryJob, startPolling, stopPolling, isLoading } =
    useJobsStore();

  // Filter to 3D jobs only
  const model3dJobs = jobs.filter((job) => job.job_type === "model3d");

  // Start polling on mount
  React.useEffect(() => {
    startPolling("model3d");
    return () => stopPolling();
  }, [startPolling, stopPolling]);

  // Handle generation
  const handleGenerate = async (data: GenerationRequest) => {
    try {
      const job = await createJob({ ...data, job_type: "model3d" });
      toast({
        type: "success",
        title: "Generation started",
        message: "Your 3D model is being generated...",
      });
    } catch (error) {
      toast({
        type: "error",
        title: "Generation failed",
        message: "Failed to start generation. Please try again.",
      });
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Generate 3D Model</h1>
        <p className="text-muted-foreground">
          Create 3D assets for your UI/UX designs using AI
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Prompt Editor */}
        <div>
          <PromptEditor
            defaultJobType="model3d"
            onSubmit={handleGenerate}
            isLoading={isLoading}
          />
        </div>

        {/* Recent Jobs */}
        <div className="space-y-4">
          <h2 className="text-xl font-semibold">Recent Generations</h2>
          <JobsList
            jobs={model3dJobs.slice(0, 10)}
            isLoading={isLoading}
            onCancel={cancelJob}
            onRetry={retryJob}
            onView={(job) => {
              if (job.result_asset_id) {
                router.push(`/assets?preview=${job.result_asset_id}`);
              }
            }}
            emptyMessage="No 3D generations yet. Try generating one!"
          />
        </div>
      </div>
    </div>
  );
}
