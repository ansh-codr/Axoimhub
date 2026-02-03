// =============================================================================
// Axiom Design Engine - AssetGallery Component
// Grid/List view for generated assets with filtering
// =============================================================================

"use client";

import * as React from "react";
import {
  Grid3X3,
  List,
  Download,
  Trash2,
  Eye,
  Image,
  Video,
  Box,
  Filter,
  Search,
  MoreVertical,
  ExternalLink,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { formatFileSize, formatRelativeTime } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
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
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type { Asset, AssetType, ViewMode } from "@/types";

// =============================================================================
// Props Interface
// =============================================================================

export interface AssetGalleryProps {
  assets: Asset[];
  viewMode?: ViewMode;
  onViewModeChange?: (mode: ViewMode) => void;
  onDownload?: (asset: Asset) => void;
  onDelete?: (asset: Asset) => Promise<void>;
  onPreview?: (asset: Asset) => void;
  filterType?: AssetType | "all";
  onFilterChange?: (type: AssetType | "all") => void;
  searchQuery?: string;
  onSearchChange?: (query: string) => void;
  isLoading?: boolean;
  emptyMessage?: string;
  className?: string;
}

// =============================================================================
// Component
// =============================================================================

export function AssetGallery({
  assets,
  viewMode = "grid",
  onViewModeChange,
  onDownload,
  onDelete,
  onPreview,
  filterType = "all",
  onFilterChange,
  searchQuery = "",
  onSearchChange,
  isLoading,
  emptyMessage = "No assets yet. Start generating!",
  className,
}: AssetGalleryProps) {
  const [previewAsset, setPreviewAsset] = React.useState<Asset | null>(null);
  const [deletingId, setDeletingId] = React.useState<string | null>(null);

  // Filter assets
  const filteredAssets = React.useMemo(() => {
    let filtered = assets;

    if (filterType !== "all") {
      filtered = filtered.filter((a) => a.asset_type === filterType);
    }

    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (a) =>
          a.filename.toLowerCase().includes(query) ||
          a.metadata?.prompt?.toLowerCase().includes(query)
      );
    }

    return filtered;
  }, [assets, filterType, searchQuery]);

  const handleDelete = async (asset: Asset) => {
    if (!onDelete) return;
    setDeletingId(asset.id);
    try {
      await onDelete(asset);
    } finally {
      setDeletingId(null);
    }
  };

  const handlePreview = (asset: Asset) => {
    if (onPreview) {
      onPreview(asset);
    } else {
      setPreviewAsset(asset);
    }
  };

  return (
    <div className={cn("space-y-4", className)}>
      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-4">
        {/* Search */}
        {onSearchChange && (
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search assets..."
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              className="pl-9"
            />
          </div>
        )}

        {/* Filter */}
        {onFilterChange && (
          <Select
            value={filterType}
            onValueChange={(v) => onFilterChange(v as AssetType | "all")}
          >
            <SelectTrigger className="w-[140px]">
              <Filter className="h-4 w-4 mr-2" />
              <SelectValue placeholder="Filter" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Types</SelectItem>
              <SelectItem value="image">Images</SelectItem>
              <SelectItem value="video">Videos</SelectItem>
              <SelectItem value="model3d">3D Models</SelectItem>
            </SelectContent>
          </Select>
        )}

        {/* View Mode Toggle */}
        {onViewModeChange && (
          <div className="flex rounded-md border">
            <Button
              variant={viewMode === "grid" ? "default" : "ghost"}
              size="icon"
              className="rounded-r-none"
              onClick={() => onViewModeChange("grid")}
            >
              <Grid3X3 className="h-4 w-4" />
            </Button>
            <Button
              variant={viewMode === "list" ? "default" : "ghost"}
              size="icon"
              className="rounded-l-none"
              onClick={() => onViewModeChange("list")}
            >
              <List className="h-4 w-4" />
            </Button>
          </div>
        )}
      </div>

      {/* Results Count */}
      <p className="text-sm text-muted-foreground">
        {filteredAssets.length} asset{filteredAssets.length !== 1 ? "s" : ""}
        {filterType !== "all" && ` (${filterType})`}
      </p>

      {/* Loading State */}
      {isLoading && (
        <div
          className={cn(
            viewMode === "grid"
              ? "grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4"
              : "space-y-2"
          )}
        >
          {[1, 2, 3, 4, 5, 6].map((i) =>
            viewMode === "grid" ? (
              <AssetCardSkeleton key={i} />
            ) : (
              <AssetListItemSkeleton key={i} />
            )
          )}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && filteredAssets.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="rounded-full bg-muted p-4 mb-4">
            <Image className="h-8 w-8 text-muted-foreground" />
          </div>
          <p className="text-muted-foreground">{emptyMessage}</p>
        </div>
      )}

      {/* Grid View */}
      {!isLoading && filteredAssets.length > 0 && viewMode === "grid" && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {filteredAssets.map((asset) => (
            <AssetCard
              key={asset.id}
              asset={asset}
              onPreview={() => handlePreview(asset)}
              onDownload={onDownload ? () => onDownload(asset) : undefined}
              onDelete={onDelete ? () => handleDelete(asset) : undefined}
              isDeleting={deletingId === asset.id}
            />
          ))}
        </div>
      )}

      {/* List View */}
      {!isLoading && filteredAssets.length > 0 && viewMode === "list" && (
        <div className="space-y-2">
          {filteredAssets.map((asset) => (
            <AssetListItem
              key={asset.id}
              asset={asset}
              onPreview={() => handlePreview(asset)}
              onDownload={onDownload ? () => onDownload(asset) : undefined}
              onDelete={onDelete ? () => handleDelete(asset) : undefined}
              isDeleting={deletingId === asset.id}
            />
          ))}
        </div>
      )}

      {/* Preview Dialog */}
      <Dialog
        open={previewAsset !== null}
        onOpenChange={(open) => !open && setPreviewAsset(null)}
      >
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>{previewAsset?.filename}</DialogTitle>
          </DialogHeader>
          {previewAsset && (
            <AssetPreviewContent
              asset={previewAsset}
              onDownload={onDownload}
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

// =============================================================================
// Asset Card (Grid View)
// =============================================================================

interface AssetCardProps {
  asset: Asset;
  onPreview: () => void;
  onDownload?: () => void;
  onDelete?: () => void;
  isDeleting?: boolean;
}

function AssetCard({
  asset,
  onPreview,
  onDownload,
  onDelete,
  isDeleting,
}: AssetCardProps) {
  const TypeIcon = getAssetTypeIcon(asset.asset_type);

  return (
    <div className="group relative rounded-lg border bg-card overflow-hidden">
      {/* Thumbnail */}
      <button
        onClick={onPreview}
        className="aspect-square w-full bg-muted/50 flex items-center justify-center overflow-hidden focus:outline-none focus:ring-2 focus:ring-axiom-500 focus:ring-inset"
      >
        {asset.thumbnail_url ? (
          <img
            src={asset.thumbnail_url}
            alt={asset.filename}
            className="h-full w-full object-cover transition-transform group-hover:scale-105"
          />
        ) : (
          <TypeIcon className="h-12 w-12 text-muted-foreground/50" />
        )}

        {/* Hover Overlay */}
        <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
          <Button size="icon" variant="secondary">
            <Eye className="h-4 w-4" />
          </Button>
          {onDownload && (
            <Button size="icon" variant="secondary" onClick={(e) => { e.stopPropagation(); onDownload(); }}>
              <Download className="h-4 w-4" />
            </Button>
          )}
        </div>
      </button>

      {/* Info */}
      <div className="p-3">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="font-medium truncate text-sm">{asset.filename}</p>
            <p className="text-xs text-muted-foreground">
              {formatFileSize(asset.file_size)}
            </p>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8 shrink-0">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={onPreview}>
                <Eye className="h-4 w-4 mr-2" />
                Preview
              </DropdownMenuItem>
              {onDownload && (
                <DropdownMenuItem onClick={onDownload}>
                  <Download className="h-4 w-4 mr-2" />
                  Download
                </DropdownMenuItem>
              )}
              {onDelete && (
                <>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onClick={onDelete}
                    disabled={isDeleting}
                    className="text-red-600 focus:text-red-600"
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete
                  </DropdownMenuItem>
                </>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Type Badge */}
      <Badge
        variant="secondary"
        className="absolute top-2 left-2 text-xs capitalize"
      >
        <TypeIcon className="h-3 w-3 mr-1" />
        {asset.asset_type}
      </Badge>
    </div>
  );
}

// =============================================================================
// Asset List Item (List View)
// =============================================================================

interface AssetListItemProps {
  asset: Asset;
  onPreview: () => void;
  onDownload?: () => void;
  onDelete?: () => void;
  isDeleting?: boolean;
}

function AssetListItem({
  asset,
  onPreview,
  onDownload,
  onDelete,
  isDeleting,
}: AssetListItemProps) {
  const TypeIcon = getAssetTypeIcon(asset.asset_type);

  return (
    <div className="flex items-center gap-4 rounded-lg border p-3 hover:bg-muted/30 transition-colors">
      {/* Thumbnail */}
      <button
        onClick={onPreview}
        className="h-16 w-16 rounded-md bg-muted/50 flex items-center justify-center overflow-hidden shrink-0 focus:outline-none focus:ring-2 focus:ring-axiom-500"
      >
        {asset.thumbnail_url ? (
          <img
            src={asset.thumbnail_url}
            alt={asset.filename}
            className="h-full w-full object-cover"
          />
        ) : (
          <TypeIcon className="h-6 w-6 text-muted-foreground/50" />
        )}
      </button>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <p className="font-medium truncate">{asset.filename}</p>
        <div className="flex items-center gap-3 text-sm text-muted-foreground">
          <span className="capitalize flex items-center gap-1">
            <TypeIcon className="h-3 w-3" />
            {asset.asset_type}
          </span>
          <span>{formatFileSize(asset.file_size)}</span>
          <span>{formatRelativeTime(new Date(asset.created_at))}</span>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-1">
        <Button variant="ghost" size="icon" onClick={onPreview}>
          <Eye className="h-4 w-4" />
        </Button>
        {onDownload && (
          <Button variant="ghost" size="icon" onClick={onDownload}>
            <Download className="h-4 w-4" />
          </Button>
        )}
        {onDelete && (
          <Button
            variant="ghost"
            size="icon"
            onClick={onDelete}
            disabled={isDeleting}
          >
            <Trash2 className="h-4 w-4 text-red-500" />
          </Button>
        )}
      </div>
    </div>
  );
}

// =============================================================================
// Asset Preview Content
// =============================================================================

interface AssetPreviewContentProps {
  asset: Asset;
  onDownload?: (asset: Asset) => void;
}

function AssetPreviewContent({ asset, onDownload }: AssetPreviewContentProps) {
  return (
    <div className="space-y-4">
      {/* Preview */}
      <div className="aspect-video bg-muted rounded-lg overflow-hidden flex items-center justify-center">
        {asset.asset_type === "image" && asset.url && (
          <img
            src={asset.url}
            alt={asset.filename}
            className="max-h-full max-w-full object-contain"
          />
        )}
        {asset.asset_type === "video" && asset.url && (
          <video
            src={asset.url}
            controls
            className="max-h-full max-w-full"
          />
        )}
        {asset.asset_type === "model3d" && (
          <div className="text-center p-8">
            <Box className="h-16 w-16 mx-auto text-muted-foreground/50 mb-4" />
            <p className="text-muted-foreground">
              3D preview requires dedicated viewer
            </p>
            {asset.url && (
              <Button
                variant="outline"
                className="mt-4"
                onClick={() => window.open(asset.url, "_blank")}
              >
                <ExternalLink className="h-4 w-4 mr-2" />
                Open in Viewer
              </Button>
            )}
          </div>
        )}
      </div>

      {/* Metadata */}
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <p className="text-muted-foreground">File Size</p>
          <p className="font-medium">{formatFileSize(asset.file_size)}</p>
        </div>
        <div>
          <p className="text-muted-foreground">Format</p>
          <p className="font-medium uppercase">{asset.format}</p>
        </div>
        {asset.metadata?.width && (
          <div>
            <p className="text-muted-foreground">Dimensions</p>
            <p className="font-medium">
              {asset.metadata.width} × {asset.metadata.height}
            </p>
          </div>
        )}
        <div>
          <p className="text-muted-foreground">Created</p>
          <p className="font-medium">
            {formatRelativeTime(new Date(asset.created_at))}
          </p>
        </div>
      </div>

      {/* Prompt */}
      {asset.metadata?.prompt && (
        <div>
          <p className="text-sm text-muted-foreground mb-1">Prompt</p>
          <p className="text-sm bg-muted/50 rounded-md p-3">
            {asset.metadata.prompt}
          </p>
        </div>
      )}

      {/* Actions */}
      {onDownload && (
        <div className="flex justify-end">
          <Button onClick={() => onDownload(asset)}>
            <Download className="h-4 w-4 mr-2" />
            Download
          </Button>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Helpers
// =============================================================================

function getAssetTypeIcon(type: AssetType) {
  switch (type) {
    case "video":
      return Video;
    case "model3d":
      return Box;
    default:
      return Image;
  }
}

// =============================================================================
// Loading Skeletons
// =============================================================================

function AssetCardSkeleton() {
  return (
    <div className="rounded-lg border overflow-hidden">
      <Skeleton className="aspect-square w-full" />
      <div className="p-3 space-y-2">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-3 w-1/2" />
      </div>
    </div>
  );
}

function AssetListItemSkeleton() {
  return (
    <div className="flex items-center gap-4 rounded-lg border p-3">
      <Skeleton className="h-16 w-16 rounded-md" />
      <div className="flex-1 space-y-2">
        <Skeleton className="h-4 w-1/3" />
        <Skeleton className="h-3 w-1/2" />
      </div>
      <Skeleton className="h-8 w-24" />
    </div>
  );
}
