// =============================================================================
// Axiom Design Engine - Dashboard Layout
// Authenticated layout with sidebar
// =============================================================================

"use client";

import * as React from "react";
import { useRequireAuth } from "@/hooks";
import { useUIStore } from "@/store";
import { cn } from "@/lib/utils";
import { Header } from "@/components/layout/header";
import { Sidebar } from "@/components/layout/sidebar";
import { Skeleton } from "@/components/ui/skeleton";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isLoading } = useRequireAuth();
  const sidebarOpen = useUIStore((state) => state.sidebarOpen);

  if (isLoading) {
    return <DashboardLayoutSkeleton />;
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <Sidebar />
      <main
        className={cn(
          "pt-16 min-h-screen transition-all duration-300",
          sidebarOpen ? "pl-64" : "pl-16"
        )}
      >
        <div className="container p-6">{children}</div>
      </main>
    </div>
  );
}

function DashboardLayoutSkeleton() {
  return (
    <div className="min-h-screen bg-background">
      {/* Header Skeleton */}
      <div className="sticky top-0 z-40 h-16 border-b bg-background">
        <div className="container flex h-full items-center justify-between px-4">
          <Skeleton className="h-8 w-32" />
          <Skeleton className="h-8 w-8 rounded-full" />
        </div>
      </div>

      {/* Sidebar Skeleton */}
      <div className="fixed left-0 top-16 z-30 h-[calc(100vh-4rem)] w-64 border-r bg-background p-4">
        <div className="space-y-4">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
          <div className="space-y-2 pt-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        </div>
      </div>

      {/* Content Skeleton */}
      <main className="pt-16 pl-64 min-h-screen">
        <div className="container p-6 space-y-6">
          <Skeleton className="h-8 w-48" />
          <div className="grid md:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-32" />
            ))}
          </div>
          <Skeleton className="h-64" />
        </div>
      </main>
    </div>
  );
}
