// =============================================================================
// Axiom Design Engine - Sidebar Component
// Collapsible sidebar for project navigation
// =============================================================================

"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  ChevronLeft,
  ChevronRight,
  Home,
  FolderKanban,
  Image,
  Video,
  Box,
  Clock,
  Settings,
  Plus,
  Search,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";

// =============================================================================
// Navigation Items
// =============================================================================

const mainNavItems = [
  { href: "/dashboard", label: "Dashboard", icon: Home },
  { href: "/projects", label: "Projects", icon: FolderKanban },
];

const assetNavItems = [
  { href: "/assets", label: "All Assets", icon: Image },
  { href: "/assets?type=image", label: "Images", icon: Image },
  { href: "/assets?type=video", label: "Videos", icon: Video },
  { href: "/assets?type=model3d", label: "3D Models", icon: Box },
];

const otherNavItems = [
  { href: "/history", label: "History", icon: Clock },
  { href: "/settings", label: "Settings", icon: Settings },
];

// =============================================================================
// Component
// =============================================================================

export interface SidebarProps {
  className?: string;
}

export function Sidebar({ className }: SidebarProps) {
  const pathname = usePathname();
  const { sidebarOpen, toggleSidebar } = useUIStore();

  return (
    <aside
      className={cn(
        "fixed left-0 top-16 z-30 h-[calc(100vh-4rem)] border-r bg-background transition-all duration-300",
        sidebarOpen ? "w-64" : "w-16",
        className
      )}
    >
      {/* Toggle Button */}
      <Button
        variant="ghost"
        size="icon"
        className="absolute -right-3 top-6 h-6 w-6 rounded-full border bg-background shadow-md"
        onClick={toggleSidebar}
      >
        {sidebarOpen ? (
          <ChevronLeft className="h-3 w-3" />
        ) : (
          <ChevronRight className="h-3 w-3" />
        )}
      </Button>

      <div className="flex h-full flex-col gap-4 p-4">
        {/* Quick Actions */}
        {sidebarOpen ? (
          <div className="space-y-2">
            <Button className="w-full justify-start gap-2" asChild>
              <Link href="/projects/new">
                <Plus className="h-4 w-4" />
                New Project
              </Link>
            </Button>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input placeholder="Search..." className="pl-9" />
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2">
            <Button size="icon" asChild>
              <Link href="/projects/new">
                <Plus className="h-4 w-4" />
              </Link>
            </Button>
            <Button variant="ghost" size="icon">
              <Search className="h-4 w-4" />
            </Button>
          </div>
        )}

        {/* Main Navigation */}
        <nav className="space-y-1">
          {sidebarOpen && (
            <p className="px-2 text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
              Main
            </p>
          )}
          {mainNavItems.map((item) => (
            <NavItem
              key={item.href}
              item={item}
              isActive={pathname === item.href}
              collapsed={!sidebarOpen}
            />
          ))}
        </nav>

        {/* Assets Navigation */}
        <nav className="space-y-1">
          {sidebarOpen && (
            <p className="px-2 text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
              Assets
            </p>
          )}
          {assetNavItems.map((item) => (
            <NavItem
              key={item.href}
              item={item}
              isActive={pathname + window.location.search === item.href}
              collapsed={!sidebarOpen}
            />
          ))}
        </nav>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Other Navigation */}
        <nav className="space-y-1">
          {otherNavItems.map((item) => (
            <NavItem
              key={item.href}
              item={item}
              isActive={pathname.startsWith(item.href)}
              collapsed={!sidebarOpen}
            />
          ))}
        </nav>
      </div>
    </aside>
  );
}

// =============================================================================
// Nav Item Component
// =============================================================================

interface NavItemProps {
  item: {
    href: string;
    label: string;
    icon: React.ComponentType<{ className?: string }>;
  };
  isActive: boolean;
  collapsed: boolean;
}

function NavItem({ item, isActive, collapsed }: NavItemProps) {
  const Icon = item.icon;

  if (collapsed) {
    return (
      <Link
        href={item.href}
        className={cn(
          "flex h-10 w-10 items-center justify-center rounded-md transition-colors",
          isActive
            ? "bg-axiom-100 text-axiom-700 dark:bg-axiom-900 dark:text-axiom-300"
            : "text-muted-foreground hover:bg-muted hover:text-foreground"
        )}
        title={item.label}
      >
        <Icon className="h-5 w-5" />
      </Link>
    );
  }

  return (
    <Link
      href={item.href}
      className={cn(
        "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
        isActive
          ? "bg-axiom-100 text-axiom-700 dark:bg-axiom-900 dark:text-axiom-300"
          : "text-muted-foreground hover:bg-muted hover:text-foreground"
      )}
    >
      <Icon className="h-5 w-5" />
      {item.label}
    </Link>
  );
}

// =============================================================================
// Sidebar Skeleton
// =============================================================================

export function SidebarSkeleton() {
  return (
    <aside className="fixed left-0 top-16 z-30 h-[calc(100vh-4rem)] w-64 border-r bg-background p-4">
      <div className="space-y-4">
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
        <div className="space-y-2 pt-4">
          {[1, 2, 3, 4, 5].map((i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </div>
      </div>
    </aside>
  );
}
