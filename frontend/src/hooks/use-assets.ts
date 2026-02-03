// =============================================================================
// Axiom Design Engine - useAssets Hook
// Asset management utilities
// =============================================================================

"use client";

import { useCallback, useEffect } from "react";
import { useAssetsStore } from "@/store";
import type { AssetType } from "@/types";

export function useAssets() {
  const {
    assets,
    currentAsset,
    isLoading,
    error,
    totalAssets,
    currentPage,
    viewMode,
    filterType,
    fetchAssets,
    fetchAsset,
    deleteAsset,
    downloadAsset,
    setViewMode,
    setFilterType,
    clearError,
    reset,
  } = useAssetsStore();

  return {
    assets,
    currentAsset,
    isLoading,
    error,
    totalAssets,
    currentPage,
    viewMode,
    filterType,
    fetchAssets,
    fetchAsset,
    deleteAsset,
    downloadAsset,
    setViewMode,
    setFilterType,
    clearError,
    reset,
  };
}

/**
 * Hook for fetching assets with filters
 */
export function useAssetsList(
  options: {
    page?: number;
    type?: AssetType;
  } = {}
) {
  const { page = 1, type } = options;
  const { assets, isLoading, error, totalAssets, fetchAssets, viewMode, setViewMode } =
    useAssetsStore();

  const refresh = useCallback(() => {
    fetchAssets(page, type);
  }, [fetchAssets, page, type]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return {
    assets,
    isLoading,
    error,
    totalAssets,
    viewMode,
    setViewMode,
    refresh,
  };
}

/**
 * Hook for downloading assets
 */
export function useAssetDownload() {
  const { downloadAsset, error, clearError } = useAssetsStore();

  const download = useCallback(
    async (assetId: string, filename?: string) => {
      const url = await downloadAsset(assetId);

      // Trigger browser download
      const link = document.createElement("a");
      link.href = url;
      link.download = filename || "download";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    },
    [downloadAsset]
  );

  return {
    download,
    error,
    clearError,
  };
}

/**
 * Hook for asset preview
 */
export function useAssetPreview(assetId: string | null) {
  const { currentAsset, isLoading, error, fetchAsset } = useAssetsStore();

  useEffect(() => {
    if (assetId) {
      fetchAsset(assetId);
    }
  }, [assetId, fetchAsset]);

  return {
    asset: currentAsset,
    isLoading,
    error,
  };
}
