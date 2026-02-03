// =============================================================================
// Axiom Design Engine - Jobs Store
// Zustand store for job management
// =============================================================================

import { create } from "zustand";
import type { Job, JobStatus, CreateJobData } from "@/types";
import { jobsApi } from "@/lib/api";

// -----------------------------------------------------------------------------
// Types
// -----------------------------------------------------------------------------

interface JobsState {
  // State
  jobs: Job[];
  currentJob: Job | null;
  isLoading: boolean;
  error: string | null;
  totalJobs: number;
  currentPage: number;

  // Polling
  pollingJobIds: Set<string>;

  // Actions
  fetchJobs: (page?: number, status?: JobStatus) => Promise<void>;
  fetchJob: (id: string) => Promise<void>;
  createJob: (data: CreateJobData) => Promise<Job>;
  cancelJob: (id: string) => Promise<void>;
  retryJob: (id: string) => Promise<void>;
  updateJobStatus: (id: string, status: JobStatus, progress?: number) => void;
  startPolling: (jobId: string) => void;
  stopPolling: (jobId: string) => void;
  clearError: () => void;
  reset: () => void;
}

// -----------------------------------------------------------------------------
// Polling Manager
// -----------------------------------------------------------------------------

const POLLING_INTERVAL = 2000;
const pollingIntervals: Map<string, NodeJS.Timeout> = new Map();

// -----------------------------------------------------------------------------
// Store
// -----------------------------------------------------------------------------

export const useJobsStore = create<JobsState>((set, get) => ({
  // Initial state
  jobs: [],
  currentJob: null,
  isLoading: false,
  error: null,
  totalJobs: 0,
  currentPage: 1,
  pollingJobIds: new Set(),

  // Fetch jobs list
  fetchJobs: async (page = 1, status?: JobStatus) => {
    set({ isLoading: true, error: null });
    try {
      const response = await jobsApi.list(page, 20, status);
      set({
        jobs: response.items,
        totalJobs: response.total,
        currentPage: page,
        isLoading: false,
      });
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to fetch jobs.";
      set({ error: message, isLoading: false });
    }
  },

  // Fetch single job
  fetchJob: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      const job = await jobsApi.get(id);
      set((state) => ({
        currentJob: job,
        jobs: state.jobs.map((j) => (j.id === id ? job : j)),
        isLoading: false,
      }));
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to fetch job.";
      set({ error: message, isLoading: false });
    }
  },

  // Create new job
  createJob: async (data: CreateJobData) => {
    set({ isLoading: true, error: null });
    try {
      const job = await jobsApi.create(data);
      set((state) => ({
        jobs: [job, ...state.jobs],
        currentJob: job,
        isLoading: false,
      }));

      // Start polling for status updates
      get().startPolling(job.id);

      return job;
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to create job.";
      set({ error: message, isLoading: false });
      throw error;
    }
  },

  // Cancel job
  cancelJob: async (id: string) => {
    set({ error: null });
    try {
      const job = await jobsApi.cancel(id);
      get().stopPolling(id);
      set((state) => ({
        jobs: state.jobs.map((j) => (j.id === id ? job : j)),
        currentJob: state.currentJob?.id === id ? job : state.currentJob,
      }));
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to cancel job.";
      set({ error: message });
    }
  },

  // Retry job
  retryJob: async (id: string) => {
    set({ error: null });
    try {
      const job = await jobsApi.retry(id);
      set((state) => ({
        jobs: state.jobs.map((j) => (j.id === id ? job : j)),
        currentJob: state.currentJob?.id === id ? job : state.currentJob,
      }));
      get().startPolling(id);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to retry job.";
      set({ error: message });
    }
  },

  // Update job status (for real-time updates)
  updateJobStatus: (id: string, status: JobStatus, progress?: number) => {
    set((state) => ({
      jobs: state.jobs.map((j) =>
        j.id === id ? { ...j, status, progress } : j
      ),
      currentJob:
        state.currentJob?.id === id
          ? { ...state.currentJob, status, progress }
          : state.currentJob,
    }));

    // Stop polling if job is complete or failed
    if (["completed", "failed", "cancelled"].includes(status)) {
      get().stopPolling(id);
    }
  },

  // Start polling for job status
  startPolling: (jobId: string) => {
    const { pollingJobIds } = get();

    if (pollingJobIds.has(jobId)) return;

    set((state) => ({
      pollingJobIds: new Set(state.pollingJobIds).add(jobId),
    }));

    const interval = setInterval(async () => {
      try {
        const { status, progress } = await jobsApi.getStatus(jobId);
        get().updateJobStatus(jobId, status as JobStatus, progress);

        // Re-fetch job to get assets when completed
        if (status === "completed") {
          get().fetchJob(jobId);
        }
      } catch {
        // Stop polling on error
        get().stopPolling(jobId);
      }
    }, POLLING_INTERVAL);

    pollingIntervals.set(jobId, interval);
  },

  // Stop polling for job status
  stopPolling: (jobId: string) => {
    const interval = pollingIntervals.get(jobId);
    if (interval) {
      clearInterval(interval);
      pollingIntervals.delete(jobId);
    }

    set((state) => {
      const newPollingIds = new Set(state.pollingJobIds);
      newPollingIds.delete(jobId);
      return { pollingJobIds: newPollingIds };
    });
  },

  // Clear error
  clearError: () => {
    set({ error: null });
  },

  // Reset store
  reset: () => {
    // Clear all polling
    pollingIntervals.forEach((interval) => clearInterval(interval));
    pollingIntervals.clear();

    set({
      jobs: [],
      currentJob: null,
      isLoading: false,
      error: null,
      totalJobs: 0,
      currentPage: 1,
      pollingJobIds: new Set(),
    });
  },
}));
