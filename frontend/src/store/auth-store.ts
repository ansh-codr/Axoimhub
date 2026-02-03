// =============================================================================
// Axiom Design Engine - Authentication Store
// Zustand store for authentication state
// =============================================================================

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { User } from "@/types";
import { authApi } from "@/lib/api";
import { setTokens, clearTokens, loadStoredToken } from "@/lib/api-client";

// -----------------------------------------------------------------------------
// Types
// -----------------------------------------------------------------------------

interface AuthState {
  // State
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  login: (email: string, password: string) => Promise<void>;
  register: (
    email: string,
    username: string,
    password: string,
    passwordConfirm: string,
    fullName?: string
  ) => Promise<void>;
  logout: () => Promise<void>;
  fetchProfile: () => Promise<void>;
  updateProfile: (data: Partial<User>) => Promise<void>;
  clearError: () => void;
  initialize: () => Promise<void>;
}

// -----------------------------------------------------------------------------
// Store
// -----------------------------------------------------------------------------

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      // Initialize auth from stored token
      initialize: async () => {
        const storedToken = loadStoredToken();
        if (!storedToken) {
          set({ isLoading: false });
          return;
        }

        set({ isLoading: true });
        try {
          // Try to refresh and get profile
          const tokens = await authApi.refresh(storedToken);
          setTokens(tokens);
          const user = await authApi.getProfile();
          set({ user, isAuthenticated: true, isLoading: false });
        } catch {
          clearTokens();
          set({ user: null, isAuthenticated: false, isLoading: false });
        }
      },

      // Login
      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null });
        try {
          const tokens = await authApi.login({ email, password });
          setTokens(tokens);
          const user = await authApi.getProfile();
          set({ user, isAuthenticated: true, isLoading: false });
        } catch (error) {
          const message =
            error instanceof Error
              ? error.message
              : "Login failed. Please check your credentials.";
          set({ error: message, isLoading: false });
          throw error;
        }
      },

      // Register
      register: async (
        email: string,
        username: string,
        password: string,
        passwordConfirm: string,
        fullName?: string
      ) => {
        set({ isLoading: true, error: null });
        try {
          await authApi.register({
            email,
            username,
            password,
            password_confirm: passwordConfirm,
            full_name: fullName,
          });
          // Auto-login after registration
          await get().login(email, password);
        } catch (error) {
          const message =
            error instanceof Error
              ? error.message
              : "Registration failed. Please try again.";
          set({ error: message, isLoading: false });
          throw error;
        }
      },

      // Logout
      logout: async () => {
        set({ isLoading: true });
        try {
          await authApi.logout();
        } catch {
          // Ignore logout errors
        } finally {
          clearTokens();
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
          });
        }
      },

      // Fetch profile
      fetchProfile: async () => {
        if (!get().isAuthenticated) return;

        set({ isLoading: true });
        try {
          const user = await authApi.getProfile();
          set({ user, isLoading: false });
        } catch (error) {
          const message =
            error instanceof Error
              ? error.message
              : "Failed to fetch profile.";
          set({ error: message, isLoading: false });
        }
      },

      // Update profile
      updateProfile: async (data: Partial<User>) => {
        set({ isLoading: true, error: null });
        try {
          const user = await authApi.updateProfile(data);
          set({ user, isLoading: false });
        } catch (error) {
          const message =
            error instanceof Error
              ? error.message
              : "Failed to update profile.";
          set({ error: message, isLoading: false });
          throw error;
        }
      },

      // Clear error
      clearError: () => {
        set({ error: null });
      },
    }),
    {
      name: "axiom-auth",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        // Only persist user data, not loading states
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
