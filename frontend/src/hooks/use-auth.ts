// =============================================================================
// Axiom Design Engine - useAuth Hook
// Authentication utilities and state
// =============================================================================

"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store";

const disableAuth =
  typeof process !== "undefined" &&
  process.env.NEXT_PUBLIC_DISABLE_AUTH === "true";

export function useAuth() {
  const {
    user,
    isAuthenticated,
    isLoading,
    error,
    login,
    logout,
    register,
    fetchProfile,
    clearError,
  } = useAuthStore();

  return {
    user,
    isAuthenticated,
    isLoading,
    error,
    login,
    logout,
    register,
    fetchProfile,
    clearError,
  };
}

/**
 * Hook to protect routes - redirects to login if not authenticated
 */
export function useRequireAuth(redirectTo = "/login") {
  const router = useRouter();
  const { isAuthenticated, isLoading, initialize } = useAuthStore();

  if (disableAuth) {
    return { isAuthenticated: true, isLoading: false };
  }

  useEffect(() => {
    initialize();
  }, [initialize]);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push(redirectTo);
    }
  }, [isAuthenticated, isLoading, redirectTo, router]);

  return { isAuthenticated, isLoading };
}

/**
 * Hook to redirect authenticated users away from auth pages
 */
export function useRedirectIfAuthenticated(redirectTo = "/dashboard") {
  const router = useRouter();
  const { isAuthenticated, isLoading, initialize } = useAuthStore();

  if (disableAuth) {
    return { isAuthenticated: false, isLoading: false };
  }

  useEffect(() => {
    initialize();
  }, [initialize]);

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.push(redirectTo);
    }
  }, [isAuthenticated, isLoading, redirectTo, router]);

  return { isAuthenticated, isLoading };
}
