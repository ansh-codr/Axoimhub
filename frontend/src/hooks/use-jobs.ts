// =============================================================================
// Axiom Design Engine - useJobs Hook
// Job management utilities
// =============================================================================

"use client";

import { useCallback, useEffect } from "react";
import { useJobsStore } from "@/store";
import type { CreateJobData, JobStatus } from "@/types";

export function useJobs() {
  const {
    jobs,
    currentJob,
    isLoading,
    error,
    totalJobs,
    currentPage,
    fetchJobs,
    fetchJob,
    createJob,
    cancelJob,
    retryJob,
    clearError,
    reset,
  } = useJobsStore();

  return {
    jobs,
    currentJob,
    isLoading,
    error,
    totalJobs,
    currentPage,
    fetchJobs,
    fetchJob,
    createJob,
    cancelJob,
    retryJob,
    clearError,
    reset,
  };
}

/**
 * Hook for fetching jobs with automatic refresh
 */
export function useJobsList(
  options: {
    page?: number;
    status?: JobStatus;
    autoRefresh?: boolean;
    refreshInterval?: number;
  } = {}
) {
  const { page = 1, status, autoRefresh = false, refreshInterval = 30000 } = options;
  const { jobs, isLoading, error, totalJobs, fetchJobs } = useJobsStore();

  const refresh = useCallback(() => {
    fetchJobs(page, status);
  }, [fetchJobs, page, status]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(refresh, refreshInterval);
    return () => clearInterval(interval);
  }, [autoRefresh, refresh, refreshInterval]);

  return {
    jobs,
    isLoading,
    error,
    totalJobs,
    refresh,
  };
}

/**
 * Hook for tracking a specific job
 */
export function useJob(jobId: string | null) {
  const { currentJob, isLoading, error, fetchJob, startPolling, stopPolling } =
    useJobsStore();

  useEffect(() => {
    if (!jobId) return;

    fetchJob(jobId);

    // Start polling if job is in progress
    if (
      currentJob &&
      ["pending", "queued", "running"].includes(currentJob.status)
    ) {
      startPolling(jobId);
    }

    return () => {
      if (jobId) stopPolling(jobId);
    };
  }, [jobId, fetchJob, startPolling, stopPolling, currentJob]);

  return {
    job: currentJob,
    isLoading,
    error,
    isInProgress:
      currentJob &&
      ["pending", "queued", "running"].includes(currentJob.status),
    isComplete: currentJob?.status === "completed",
    isFailed: currentJob?.status === "failed",
  };
}

/**
 * Hook for creating generation jobs
 */
export function useGenerate() {
  const { createJob, isLoading, error, clearError } = useJobsStore();

  const generateImage = useCallback(
    async (projectId: string, prompt: string, parameters?: Record<string, unknown>) => {
      const jobData: CreateJobData = {
        project_id: projectId,
        job_type: "image",
        prompt,
        parameters,
      };
      return createJob(jobData);
    },
    [createJob]
  );

  const generateVideo = useCallback(
    async (projectId: string, prompt: string, parameters?: Record<string, unknown>) => {
      const jobData: CreateJobData = {
        project_id: projectId,
        job_type: "video",
        prompt,
        parameters,
      };
      return createJob(jobData);
    },
    [createJob]
  );

  const generate3D = useCallback(
    async (projectId: string, prompt: string, parameters?: Record<string, unknown>) => {
      const jobData: CreateJobData = {
        project_id: projectId,
        job_type: "model3d",
        prompt,
        parameters,
      };
      return createJob(jobData);
    },
    [createJob]
  );

  return {
    generateImage,
    generateVideo,
    generate3D,
    isLoading,
    error,
    clearError,
  };
}
