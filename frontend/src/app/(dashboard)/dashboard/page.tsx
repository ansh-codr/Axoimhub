// =============================================================================
// Axiom Design Engine - Dashboard Page
// Main dashboard with overview and quick actions
// =============================================================================

"use client";

import * as React from "react";
import Link from "next/link";
import {
  Plus,
  Image,
  Video,
  Box,
  Clock,
  ArrowRight,
  Sparkles,
  TrendingUp,
  FolderKanban,
} from "lucide-react";
import { useAuthStore, useJobsStore, useAssetsStore } from "@/store";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { JobsList } from "@/components/generation/job-status-panel";

// =============================================================================
// Stats Cards Data
// =============================================================================

const statsCards = [
  {
    title: "Images Generated",
    icon: Image,
    value: "1,234",
    change: "+12% from last month",
    href: "/assets?type=image",
  },
  {
    title: "Videos Created",
    icon: Video,
    value: "56",
    change: "+8% from last month",
    href: "/assets?type=video",
  },
  {
    title: "3D Models",
    icon: Box,
    value: "89",
    change: "+23% from last month",
    href: "/assets?type=model3d",
  },
  {
    title: "Active Projects",
    icon: FolderKanban,
    value: "12",
    change: "3 new this week",
    href: "/projects",
  },
];

// =============================================================================
// Quick Actions
// =============================================================================

const quickActions = [
  {
    title: "Generate Image",
    description: "Create AI-powered images and illustrations",
    icon: Image,
    href: "/generate/image",
    color: "bg-blue-500",
  },
  {
    title: "Create Video",
    description: "Generate short animated videos",
    icon: Video,
    href: "/generate/video",
    color: "bg-purple-500",
  },
  {
    title: "Build 3D Model",
    description: "Generate 3D assets and textures",
    icon: Box,
    href: "/generate/3d",
    color: "bg-orange-500",
  },
];

// =============================================================================
// Page Component
// =============================================================================

export default function DashboardPage() {
  const user = useAuthStore((state) => state.user);
  const { jobs, fetchJobs, isLoading: jobsLoading } = useJobsStore();
  const { assets, fetchAssets, isLoading: assetsLoading } = useAssetsStore();

  // Fetch recent data
  React.useEffect(() => {
    fetchJobs(1);
    fetchAssets(1);
  }, [fetchJobs, fetchAssets]);

  const recentJobs = jobs.slice(0, 5);

  return (
    <div className="space-y-8">
      {/* Welcome Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            Welcome back, {user?.username || "User"}!
          </h1>
          <p className="text-muted-foreground">
            Here&apos;s an overview of your design generation activity.
          </p>
        </div>
        <Button asChild>
          <Link href="/projects/new">
            <Plus className="h-4 w-4 mr-2" />
            New Project
          </Link>
        </Button>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {statsCards.map((stat) => (
          <Link key={stat.title} href={stat.href}>
            <Card className="hover:shadow-md transition-shadow cursor-pointer">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  {stat.title}
                </CardTitle>
                <stat.icon className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
                <p className="text-xs text-muted-foreground flex items-center mt-1">
                  <TrendingUp className="h-3 w-3 mr-1 text-green-500" />
                  {stat.change}
                </p>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
        <div className="grid gap-4 md:grid-cols-3">
          {quickActions.map((action) => (
            <Link key={action.title} href={action.href}>
              <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
                <CardContent className="p-6 flex items-start gap-4">
                  <div
                    className={`${action.color} p-3 rounded-lg text-white shrink-0`}
                  >
                    <action.icon className="h-6 w-6" />
                  </div>
                  <div>
                    <h3 className="font-semibold">{action.title}</h3>
                    <p className="text-sm text-muted-foreground">
                      {action.description}
                    </p>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </div>

      {/* Recent Activity */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Recent Jobs */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Recent Jobs</CardTitle>
              <CardDescription>Your latest generation tasks</CardDescription>
            </div>
            <Button variant="ghost" size="sm" asChild>
              <Link href="/history">
                View all
                <ArrowRight className="h-4 w-4 ml-1" />
              </Link>
            </Button>
          </CardHeader>
          <CardContent>
            <JobsList
              jobs={recentJobs}
              isLoading={jobsLoading}
              emptyMessage="No recent jobs. Start generating!"
            />
          </CardContent>
        </Card>

        {/* Tips & Updates */}
        <Card>
          <CardHeader>
            <CardTitle>Tips & Updates</CardTitle>
            <CardDescription>Get the most out of Axiom</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-4 p-4 rounded-lg bg-axiom-50 dark:bg-axiom-950/30 border border-axiom-200 dark:border-axiom-800">
              <Sparkles className="h-5 w-5 text-axiom-600 shrink-0 mt-0.5" />
              <div>
                <h4 className="font-medium text-sm">Prompt Engineering Tips</h4>
                <p className="text-sm text-muted-foreground mt-1">
                  Use detailed, specific prompts for better results. Include
                  style, mood, and composition details.
                </p>
                <Button variant="link" size="sm" className="px-0 mt-1" asChild>
                  <Link href="/docs/prompt-guide">Learn more →</Link>
                </Button>
              </div>
            </div>

            <div className="flex gap-4 p-4 rounded-lg bg-muted/50 border">
              <Clock className="h-5 w-5 text-muted-foreground shrink-0 mt-0.5" />
              <div>
                <h4 className="font-medium text-sm">New: Video Generation</h4>
                <p className="text-sm text-muted-foreground mt-1">
                  Create short animated videos with our new video diffusion
                  models. Perfect for UI animations and motion graphics.
                </p>
                <Button variant="link" size="sm" className="px-0 mt-1" asChild>
                  <Link href="/generate/video">Try it now →</Link>
                </Button>
              </div>
            </div>

            <div className="flex gap-4 p-4 rounded-lg bg-muted/50 border">
              <Box className="h-5 w-5 text-muted-foreground shrink-0 mt-0.5" />
              <div>
                <h4 className="font-medium text-sm">3D Model Export</h4>
                <p className="text-sm text-muted-foreground mt-1">
                  Export your generated 3D models in GLB, OBJ, or FBX formats
                  for use in games, AR/VR, and more.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
