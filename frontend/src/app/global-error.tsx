// =============================================================================
// Axiom Design Engine - Global Error Page
// Error boundary for the app
// =============================================================================

"use client";

import * as React from "react";
import { AlertTriangle, RefreshCw, Home } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  React.useEffect(() => {
    // Log the error to an error reporting service
    console.error("Global error:", error);
  }, [error]);

  return (
    <html>
      <body>
        <div className="min-h-screen flex flex-col items-center justify-center p-4 bg-background">
          <div className="text-center">
            {/* Icon */}
            <div className="inline-flex items-center justify-center h-16 w-16 rounded-full bg-red-100 dark:bg-red-900/30 mb-8">
              <AlertTriangle className="h-8 w-8 text-red-600" />
            </div>

            {/* Error Message */}
            <h1 className="text-2xl font-semibold mb-2">Something went wrong</h1>
            <p className="text-muted-foreground max-w-md mx-auto mb-8">
              An unexpected error occurred. Our team has been notified.
              Please try again or return to the homepage.
            </p>

            {/* Error Details (dev only) */}
            {process.env.NODE_ENV === "development" && (
              <div className="mb-8 p-4 rounded-lg bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 max-w-lg mx-auto text-left">
                <p className="font-mono text-sm text-red-600 dark:text-red-400 break-words">
                  {error.message}
                </p>
                {error.digest && (
                  <p className="mt-2 font-mono text-xs text-muted-foreground">
                    Error ID: {error.digest}
                  </p>
                )}
              </div>
            )}

            {/* Actions */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Button onClick={reset}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Try Again
              </Button>
              <Button variant="outline" asChild>
                <a href="/">
                  <Home className="h-4 w-4 mr-2" />
                  Go Home
                </a>
              </Button>
            </div>
          </div>
        </div>
      </body>
    </html>
  );
}
