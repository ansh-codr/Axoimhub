// =============================================================================
// Axiom Design Engine - JobStatusPanel Component
// Displays job progress and status with real-time updates
// =============================================================================

"use client";

import * as React from "react";
import {
  Clock,
  CheckCircle2,
  XCircle,
  Loader2,
  AlertTriangle,
  Play,
  Pause,
  RotateCcw,
  X,
  Image,
  Video,
  Box,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { formatDuration, formatRelativeTime } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { Job, JobStatus, JobType } from "@/types";

// =============================================================================
// Props Interface
// =============================================================================

export interface JobStatusPanelProps {
  job: Job;
  onCancel?: (jobId: string) => Promise<void>;
  onRetry?: (jobId: string) => Promise<void>;
  onViewAsset?: (assetId: string) => void;
  showPrompt?: boolean;
  compact?: boolean;
  className?: string;
}

// =============================================================================
// Component
// =============================================================================

export function JobStatusPanel({
  job,
  onCancel,
  onRetry,
  onViewAsset,
  showPrompt = true,
  compact = false,
  className,
}: JobStatusPanelProps) {
  const [isCancelling, setIsCancelling] = React.useState(false);
  const [isRetrying, setIsRetrying] = React.useState(false);

  const handleCancel = async () => {
    if (!onCancel) return;
    setIsCancelling(true);
    try {
      await onCancel(job.id);
    } finally {
      setIsCancelling(false);
    }
  };

  const handleRetry = async () => {
    if (!onRetry) return;
    setIsRetrying(true);
    try {
      await onRetry(job.id);
    } finally {
      setIsRetrying(false);
    }
  };

  const statusConfig = getStatusConfig(job.status);
  const JobTypeIcon = getJobTypeIcon(job.job_type);

  if (compact) {
    return (
      <div
        className={cn(
          "flex items-center gap-4 rounded-lg border p-4",
          statusConfig.bgColor,
          className
        )}
      >
        <div className={cn("p-2 rounded-full", statusConfig.iconBg)}>
          <statusConfig.icon
            className={cn("h-4 w-4", statusConfig.iconColor)}
          />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <JobTypeIcon className="h-4 w-4 text-muted-foreground" />
            <span className="font-medium truncate">
              {job.prompt.slice(0, 50)}
              {job.prompt.length > 50 ? "..." : ""}
            </span>
          </div>
          {job.status === "running" && (
            <Progress value={job.progress} className="h-1 mt-2" />
          )}
        </div>

        <Badge variant={statusConfig.badgeVariant}>{job.status}</Badge>

        {canCancel(job.status) && onCancel && (
          <Button
            size="icon"
            variant="ghost"
            onClick={handleCancel}
            disabled={isCancelling}
          >
            <X className="h-4 w-4" />
          </Button>
        )}
      </div>
    );
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className={cn("p-2 rounded-full", statusConfig.iconBg)}>
              <statusConfig.icon
                className={cn("h-5 w-5", statusConfig.iconColor)}
              />
            </div>
            <div>
              <CardTitle className="text-base flex items-center gap-2">
                <JobTypeIcon className="h-4 w-4" />
                {getJobTypeLabel(job.job_type)} Generation
              </CardTitle>
              <CardDescription>
                {formatRelativeTime(new Date(job.created_at))}
              </CardDescription>
            </div>
          </div>
          <Badge variant={statusConfig.badgeVariant} className="capitalize">
            {job.status}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Prompt */}
        {showPrompt && (
          <div className="space-y-1">
            <p className="text-sm font-medium text-muted-foreground">Prompt</p>
            <p className="text-sm bg-muted/50 rounded-md p-3">{job.prompt}</p>
          </div>
        )}

        {/* Progress */}
        {job.status === "running" && (
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Progress</span>
              <span>{Math.round(job.progress)}%</span>
            </div>
            <Progress value={job.progress} />
            {job.current_step && (
              <p className="text-xs text-muted-foreground">
                {job.current_step}
              </p>
            )}
          </div>
        )}

        {/* Timing Information */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          {job.started_at && (
            <div>
              <p className="text-muted-foreground">Started</p>
              <p>{formatRelativeTime(new Date(job.started_at))}</p>
            </div>
          )}
          {job.completed_at && (
            <div>
              <p className="text-muted-foreground">Completed</p>
              <p>{formatRelativeTime(new Date(job.completed_at))}</p>
            </div>
          )}
          {job.started_at && job.completed_at && (
            <div>
              <p className="text-muted-foreground">Duration</p>
              <p>
                {formatDuration(
                  (new Date(job.completed_at).getTime() -
                    new Date(job.started_at).getTime()) /
                    1000
                )}
              </p>
            </div>
          )}
        </div>

        {/* Error Message */}
        {job.status === "failed" && job.error_message && (
          <div className="rounded-md bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 p-3">
            <div className="flex items-start gap-2">
              <AlertTriangle className="h-4 w-4 text-red-500 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-red-800 dark:text-red-200">
                  Error
                </p>
                <p className="text-sm text-red-700 dark:text-red-300">
                  {job.error_message}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-2 pt-2">
          {canCancel(job.status) && onCancel && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleCancel}
              disabled={isCancelling}
            >
              {isCancelling ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <X className="h-4 w-4 mr-2" />
              )}
              Cancel
            </Button>
          )}

          {job.status === "failed" && onRetry && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleRetry}
              disabled={isRetrying}
            >
              {isRetrying ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <RotateCcw className="h-4 w-4 mr-2" />
              )}
              Retry
            </Button>
          )}

          {job.status === "completed" && job.asset_id && onViewAsset && (
            <Button size="sm" onClick={() => onViewAsset(job.asset_id!)}>
              View Result
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// =============================================================================
// Jobs List Component
// =============================================================================

export interface JobsListProps {
  jobs: Job[];
  onCancel?: (jobId: string) => Promise<void>;
  onRetry?: (jobId: string) => Promise<void>;
  onViewAsset?: (assetId: string) => void;
  emptyMessage?: string;
  isLoading?: boolean;
  className?: string;
}

export function JobsList({
  jobs,
  onCancel,
  onRetry,
  onViewAsset,
  emptyMessage = "No jobs yet",
  isLoading,
  className,
}: JobsListProps) {
  if (isLoading) {
    return (
      <div className={cn("space-y-3", className)}>
        {[1, 2, 3].map((i) => (
          <JobStatusSkeleton key={i} />
        ))}
      </div>
    );
  }

  if (jobs.length === 0) {
    return (
      <div
        className={cn(
          "flex flex-col items-center justify-center py-12 text-center",
          className
        )}
      >
        <Clock className="h-12 w-12 text-muted-foreground/50 mb-4" />
        <p className="text-muted-foreground">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className={cn("space-y-3", className)}>
      {jobs.map((job) => (
        <JobStatusPanel
          key={job.id}
          job={job}
          onCancel={onCancel}
          onRetry={onRetry}
          onViewAsset={onViewAsset}
          compact
        />
      ))}
    </div>
  );
}

// =============================================================================
// Helpers
// =============================================================================

function getStatusConfig(status: JobStatus) {
  const configs = {
    pending: {
      icon: Clock,
      iconColor: "text-yellow-600",
      iconBg: "bg-yellow-100 dark:bg-yellow-900/30",
      bgColor: "bg-yellow-50/50 dark:bg-yellow-950/20",
      badgeVariant: "warning" as const,
    },
    queued: {
      icon: Clock,
      iconColor: "text-blue-600",
      iconBg: "bg-blue-100 dark:bg-blue-900/30",
      bgColor: "bg-blue-50/50 dark:bg-blue-950/20",
      badgeVariant: "info" as const,
    },
    running: {
      icon: Loader2,
      iconColor: "text-axiom-600 animate-spin",
      iconBg: "bg-axiom-100 dark:bg-axiom-900/30",
      bgColor: "bg-axiom-50/50 dark:bg-axiom-950/20",
      badgeVariant: "default" as const,
    },
    completed: {
      icon: CheckCircle2,
      iconColor: "text-green-600",
      iconBg: "bg-green-100 dark:bg-green-900/30",
      bgColor: "bg-green-50/50 dark:bg-green-950/20",
      badgeVariant: "success" as const,
    },
    failed: {
      icon: XCircle,
      iconColor: "text-red-600",
      iconBg: "bg-red-100 dark:bg-red-900/30",
      bgColor: "bg-red-50/50 dark:bg-red-950/20",
      badgeVariant: "destructive" as const,
    },
    cancelled: {
      icon: X,
      iconColor: "text-gray-600",
      iconBg: "bg-gray-100 dark:bg-gray-900/30",
      bgColor: "bg-gray-50/50 dark:bg-gray-950/20",
      badgeVariant: "secondary" as const,
    },
  };

  return configs[status] || configs.pending;
}

function getJobTypeIcon(jobType: JobType) {
  switch (jobType) {
    case "video":
      return Video;
    case "model3d":
      return Box;
    default:
      return Image;
  }
}

function getJobTypeLabel(jobType: JobType): string {
  switch (jobType) {
    case "video":
      return "Video";
    case "model3d":
      return "3D Model";
    default:
      return "Image";
  }
}

function canCancel(status: JobStatus): boolean {
  return ["pending", "queued", "running"].includes(status);
}

// =============================================================================
// Loading Skeleton
// =============================================================================

export function JobStatusSkeleton() {
  return (
    <div className="flex items-center gap-4 rounded-lg border p-4">
      <Skeleton className="h-10 w-10 rounded-full" />
      <div className="flex-1 space-y-2">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-2 w-full" />
      </div>
      <Skeleton className="h-6 w-16 rounded-full" />
    </div>
  );
}
