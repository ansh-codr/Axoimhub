// =============================================================================
// Axiom Design Engine - Assets Store
// Zustand store for asset management
// =============================================================================

import { create } from "zustand";
import type { Asset, AssetType } from "@/types";
import { assetsApi } from "@/lib/api";

// -----------------------------------------------------------------------------
// Types
// -----------------------------------------------------------------------------

type ViewMode = "grid" | "list";

interface AssetsState {
  // State
  assets: Asset[];
  currentAsset: Asset | null;
  isLoading: boolean;
  error: string | null;
  totalAssets: number;
  currentPage: number;

  // View settings
  viewMode: ViewMode;
  filterType: AssetType | null;

  // Actions
  fetchAssets: (page?: number, type?: AssetType) => Promise<void>;
  fetchAsset: (id: string) => Promise<void>;
  deleteAsset: (id: string) => Promise<void>;
  downloadAsset: (id: string) => Promise<string>;
  setViewMode: (mode: ViewMode) => void;
  setFilterType: (type: AssetType | null) => void;
  addAsset: (asset: Asset) => void;
  clearError: () => void;
  reset: () => void;
}

// -----------------------------------------------------------------------------
// Store
// -----------------------------------------------------------------------------

export const useAssetsStore = create<AssetsState>((set, get) => ({
  // Initial state
  assets: [],
  currentAsset: null,
  isLoading: false,
  error: null,
  totalAssets: 0,
  currentPage: 1,
  viewMode: "grid",
  filterType: null,

  // Fetch assets list
  fetchAssets: async (page = 1, type?: AssetType) => {
    set({ isLoading: true, error: null });
    try {
      const response = await assetsApi.list(page, 20, type);
      set({
        assets: response.items,
        totalAssets: response.total,
        currentPage: page,
        filterType: type || null,
        isLoading: false,
      });
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to fetch assets.";
      set({ error: message, isLoading: false });
    }
  },

  // Fetch single asset
  fetchAsset: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      const asset = await assetsApi.get(id);
      set({ currentAsset: asset, isLoading: false });
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to fetch asset.";
      set({ error: message, isLoading: false });
    }
  },

  // Delete asset
  deleteAsset: async (id: string) => {
    set({ error: null });
    try {
      await assetsApi.delete(id);
      set((state) => ({
        assets: state.assets.filter((a) => a.id !== id),
        currentAsset: state.currentAsset?.id === id ? null : state.currentAsset,
        totalAssets: state.totalAssets - 1,
      }));
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to delete asset.";
      set({ error: message });
      throw error;
    }
  },

  // Download asset
  downloadAsset: async (id: string) => {
    try {
      const { url } = await assetsApi.download(id);
      return url;
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to get download URL.";
      set({ error: message });
      throw error;
    }
  },

  // Set view mode
  setViewMode: (mode: ViewMode) => {
    set({ viewMode: mode });
  },

  // Set filter type
  setFilterType: (type: AssetType | null) => {
    set({ filterType: type });
    get().fetchAssets(1, type || undefined);
  },

  // Add asset (for real-time updates)
  addAsset: (asset: Asset) => {
    set((state) => ({
      assets: [asset, ...state.assets],
      totalAssets: state.totalAssets + 1,
    }));
  },

  // Clear error
  clearError: () => {
    set({ error: null });
  },

  // Reset store
  reset: () => {
    set({
      assets: [],
      currentAsset: null,
      isLoading: false,
      error: null,
      totalAssets: 0,
      currentPage: 1,
      viewMode: "grid",
      filterType: null,
    });
  },
}));
