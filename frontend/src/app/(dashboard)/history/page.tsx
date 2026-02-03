// =============================================================================
// Axiom Design Engine - History Page
// View all job history
// =============================================================================

"use client";

import * as React from "react";
import { useJobsStore, useToast } from "@/store";
import { JobsList } from "@/components/generation/job-status-panel";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { JobStatus } from "@/types";

export default function HistoryPage() {
  const { toast } = useToast();
  const { jobs, fetchJobs, cancelJob, retryJob, isLoading } = useJobsStore();
  const [statusFilter, setStatusFilter] = React.useState<JobStatus | "all">("all");

  // Fetch jobs
  React.useEffect(() => {
    fetchJobs(1, statusFilter === "all" ? undefined : statusFilter);
  }, [fetchJobs, statusFilter]);

  // Handle cancel
  const handleCancel = async (jobId: string) => {
    try {
      await cancelJob(jobId);
      toast({
        type: "success",
        title: "Job cancelled",
        message: "The job has been cancelled.",
      });
    } catch (error) {
      toast({
        type: "error",
        title: "Failed to cancel job",
        message: "Please try again.",
      });
    }
  };

  // Handle retry
  const handleRetry = async (jobId: string) => {
    try {
      await retryJob(jobId);
      toast({
        type: "success",
        title: "Job restarted",
        message: "The job has been queued for retry.",
      });
    } catch (error) {
      toast({
        type: "error",
        title: "Failed to retry job",
        message: "Please try again.",
      });
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">History</h1>
          <p className="text-muted-foreground">
            View all your generation job history
          </p>
        </div>

        {/* Status Filter */}
        <Select
          value={statusFilter}
          onValueChange={(v) => setStatusFilter(v as JobStatus | "all")}
        >
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="queued">Queued</SelectItem>
            <SelectItem value="running">Running</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
            <SelectItem value="failed">Failed</SelectItem>
            <SelectItem value="cancelled">Cancelled</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Jobs List */}
      <JobsList
        jobs={jobs}
        isLoading={isLoading}
        onCancel={handleCancel}
        onRetry={handleRetry}
        emptyMessage={
          statusFilter === "all"
            ? "No jobs yet. Start generating to see your history!"
            : `No ${statusFilter} jobs found.`
        }
      />
    </div>
  );
}
