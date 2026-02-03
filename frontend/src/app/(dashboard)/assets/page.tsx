// =============================================================================
// Axiom Design Engine - Assets Page
// Browse and manage all generated assets
// =============================================================================

"use client";

import * as React from "react";
import { useSearchParams } from "next/navigation";
import { useAssetsStore, useToast } from "@/store";
import { AssetGallery } from "@/components/generation/asset-gallery";
import type { AssetType } from "@/types";

export default function AssetsPage() {
  const searchParams = useSearchParams();
  const { toast } = useToast();
  const typeParam = searchParams.get("type") as AssetType | null;

  const {
    assets,
    fetchAssets,
    deleteAsset,
    downloadAsset,
    viewMode,
    setViewMode,
    filterType,
    setFilterType,
    isLoading,
  } = useAssetsStore();

  const [searchQuery, setSearchQuery] = React.useState("");

  // Set filter from URL param
  React.useEffect(() => {
    if (typeParam && ["image", "video", "model3d"].includes(typeParam)) {
      setFilterType(typeParam);
    }
  }, [typeParam, setFilterType]);

  // Fetch assets
  React.useEffect(() => {
    fetchAssets(1, filterType === "all" ? undefined : filterType);
  }, [fetchAssets, filterType]);

  // Handle download
  const handleDownload = async (asset: { id: string; filename: string }) => {
    try {
      const url = await downloadAsset(asset.id);
      const link = document.createElement("a");
      link.href = url;
      link.download = asset.filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      toast({
        type: "success",
        title: "Download started",
        message: `Downloading ${asset.filename}`,
      });
    } catch (error) {
      toast({
        type: "error",
        title: "Download failed",
        message: "Failed to download asset.",
      });
    }
  };

  // Handle delete
  const handleDelete = async (asset: { id: string; filename: string }) => {
    try {
      await deleteAsset(asset.id);
      toast({
        type: "success",
        title: "Asset deleted",
        message: `"${asset.filename}" has been deleted.`,
      });
    } catch (error) {
      toast({
        type: "error",
        title: "Delete failed",
        message: "Failed to delete asset.",
      });
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Assets</h1>
        <p className="text-muted-foreground">
          Browse and manage all your generated assets
        </p>
      </div>

      {/* Asset Gallery */}
      <AssetGallery
        assets={assets}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
        filterType={filterType}
        onFilterChange={setFilterType}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        onDownload={handleDownload}
        onDelete={handleDelete}
        isLoading={isLoading}
        emptyMessage="No assets yet. Start generating to see your creations here!"
      />
    </div>
  );
}
