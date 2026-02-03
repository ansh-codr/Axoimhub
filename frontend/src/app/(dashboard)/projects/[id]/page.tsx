// =============================================================================
// Axiom Design Engine - Project Detail Page
// Individual project with generation and assets
// =============================================================================

"use client";

import * as React from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Settings,
  Trash2,
  MoreVertical,
} from "lucide-react";
import { api } from "@/lib/api";
import { useToast, useJobsStore, useAssetsStore } from "@/store";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { PromptEditor, PromptEditorSkeleton } from "@/components/generation/prompt-editor";
import { JobsList } from "@/components/generation/job-status-panel";
import { AssetGallery } from "@/components/generation/asset-gallery";
import type { Project, JobType } from "@/types";

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const projectId = params.id as string;

  const [project, setProject] = React.useState<Project | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);
  const [deleteDialogOpen, setDeleteDialogOpen] = React.useState(false);
  const [isDeleting, setIsDeleting] = React.useState(false);

  const {
    jobs,
    fetchJobs,
    createJob,
    cancelJob,
    retryJob,
    isLoading: jobsLoading,
  } = useJobsStore();

  const {
    assets,
    fetchAssets,
    deleteAsset,
    downloadAsset,
    viewMode,
    setViewMode,
    filterType,
    setFilterType,
    isLoading: assetsLoading,
  } = useAssetsStore();

  // Fetch project
  React.useEffect(() => {
    const loadProject = async () => {
      try {
        setIsLoading(true);
        const data = await api.projectsApi.get(projectId);
        setProject(data);
      } catch (error) {
        toast({
          type: "error",
          title: "Failed to load project",
          message: "The project may not exist or you don't have access.",
        });
        router.push("/projects");
      } finally {
        setIsLoading(false);
      }
    };

    loadProject();
  }, [projectId, router, toast]);

  // Fetch jobs and assets for this project
  React.useEffect(() => {
    if (!project) return;
    fetchJobs(1); // In real implementation, filter by project
    fetchAssets(1);
  }, [project, fetchJobs, fetchAssets]);

  // Handle generation
  const handleGenerate = async (
    jobType: JobType,
    prompt: string,
    parameters: Record<string, unknown>
  ) => {
    try {
      const job = await createJob({
        project_id: projectId,
        job_type: jobType,
        prompt,
        parameters,
      });
      toast({
        type: "success",
        title: "Generation started",
        message: `Your ${jobType} is being generated.`,
      });
    } catch (error) {
      toast({
        type: "error",
        title: "Generation failed",
        message: "Failed to start generation. Please try again.",
      });
    }
  };

  // Handle delete project
  const handleDeleteProject = async () => {
    try {
      setIsDeleting(true);
      await api.projectsApi.delete(projectId);
      toast({
        type: "success",
        title: "Project deleted",
        message: `"${project?.name}" has been deleted.`,
      });
      router.push("/projects");
    } catch (error) {
      toast({
        type: "error",
        title: "Failed to delete project",
        message: "Please try again.",
      });
    } finally {
      setIsDeleting(false);
    }
  };

  // Handle asset actions
  const handleDownloadAsset = async (asset: { id: string; filename: string }) => {
    try {
      const url = await downloadAsset(asset.id);
      const link = document.createElement("a");
      link.href = url;
      link.download = asset.filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      toast({
        type: "error",
        title: "Download failed",
        message: "Failed to download asset.",
      });
    }
  };

  const handleDeleteAsset = async (asset: { id: string }) => {
    try {
      await deleteAsset(asset.id);
      toast({
        type: "success",
        title: "Asset deleted",
        message: "Asset has been removed.",
      });
    } catch (error) {
      toast({
        type: "error",
        title: "Delete failed",
        message: "Failed to delete asset.",
      });
    }
  };

  if (isLoading) {
    return <ProjectDetailSkeleton />;
  }

  if (!project) {
    return null;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" asChild>
            <Link href="/projects">
              <ArrowLeft className="h-4 w-4" />
            </Link>
          </Button>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">{project.name}</h1>
            {project.description && (
              <p className="text-muted-foreground">{project.description}</p>
            )}
          </div>
        </div>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="icon">
              <MoreVertical className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem asChild>
              <Link href={`/projects/${projectId}/settings`}>
                <Settings className="h-4 w-4 mr-2" />
                Settings
              </Link>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={() => setDeleteDialogOpen(true)}
              className="text-red-600 focus:text-red-600"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Delete Project
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Main Content */}
      <Tabs defaultValue="generate" className="space-y-6">
        <TabsList>
          <TabsTrigger value="generate">Generate</TabsTrigger>
          <TabsTrigger value="jobs">Jobs ({jobs.length})</TabsTrigger>
          <TabsTrigger value="assets">Assets ({assets.length})</TabsTrigger>
        </TabsList>

        {/* Generate Tab */}
        <TabsContent value="generate" className="space-y-6">
          <div className="grid lg:grid-cols-2 gap-6">
            <PromptEditor
              projectId={projectId}
              onGenerate={handleGenerate}
              isGenerating={jobsLoading}
            />

            <div className="space-y-4">
              <h3 className="font-semibold">Recent Jobs</h3>
              <JobsList
                jobs={jobs.slice(0, 5)}
                isLoading={jobsLoading}
                onCancel={cancelJob}
                onRetry={retryJob}
                emptyMessage="No jobs yet. Start generating!"
              />
            </div>
          </div>
        </TabsContent>

        {/* Jobs Tab */}
        <TabsContent value="jobs">
          <JobsList
            jobs={jobs}
            isLoading={jobsLoading}
            onCancel={cancelJob}
            onRetry={retryJob}
            emptyMessage="No jobs yet. Start generating!"
          />
        </TabsContent>

        {/* Assets Tab */}
        <TabsContent value="assets">
          <AssetGallery
            assets={assets}
            viewMode={viewMode}
            onViewModeChange={setViewMode}
            filterType={filterType}
            onFilterChange={setFilterType}
            onDownload={handleDownloadAsset}
            onDelete={handleDeleteAsset}
            isLoading={assetsLoading}
          />
        </TabsContent>
      </Tabs>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Project</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete &quot;{project.name}&quot;? This action
              cannot be undone. All associated assets will also be deleted.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDeleteDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeleteProject}
              disabled={isDeleting}
              isLoading={isDeleting}
            >
              Delete Project
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// =============================================================================
// Loading Skeleton
// =============================================================================

function ProjectDetailSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Skeleton className="h-10 w-10" />
        <div className="space-y-2">
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-4 w-64" />
        </div>
      </div>

      <Skeleton className="h-10 w-64" />

      <div className="grid lg:grid-cols-2 gap-6">
        <PromptEditorSkeleton />
        <div className="space-y-4">
          <Skeleton className="h-6 w-32" />
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-20" />
          ))}
        </div>
      </div>
    </div>
  );
}
