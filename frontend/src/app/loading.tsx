// =============================================================================
// Axiom Design Engine - Loading Page
// Global loading state
// =============================================================================

import { Loader2 } from "lucide-react";

export default function Loading() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center">
      <div className="text-center">
        <div className="inline-flex items-center justify-center h-12 w-12 rounded-xl bg-gradient-to-br from-axiom-500 to-axiom-700 mb-4">
          <span className="text-white font-bold text-xl">A</span>
        </div>
        <Loader2 className="h-8 w-8 animate-spin text-axiom-500 mx-auto" />
        <p className="mt-4 text-sm text-muted-foreground">Loading...</p>
      </div>
    </div>
  );
}
