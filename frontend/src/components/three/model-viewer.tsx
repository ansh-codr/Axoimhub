// =============================================================================
// Axiom Design Engine - ModelViewer Component
// Three.js based 3D model viewer with orbit controls
// =============================================================================

"use client";

import * as React from "react";
import dynamic from "next/dynamic";
import {
  RotateCcw,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Download,
  Loader2,
  AlertTriangle,
  Box,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

// =============================================================================
// Props Interface
// =============================================================================

export interface ModelViewerProps {
  src: string;
  format?: "glb" | "gltf" | "obj" | "fbx";
  autoRotate?: boolean;
  backgroundColor?: string;
  onLoad?: () => void;
  onError?: (error: Error) => void;
  onDownload?: () => void;
  className?: string;
}

// =============================================================================
// Lazy-loaded Three.js Canvas
// =============================================================================

const ThreeCanvas = dynamic(
  () => import("./model-viewer-canvas").then((mod) => mod.ModelViewerCanvas),
  {
    ssr: false,
    loading: () => <ModelViewerSkeleton />,
  }
);

// =============================================================================
// Main Component
// =============================================================================

export function ModelViewer({
  src,
  format = "glb",
  autoRotate: initialAutoRotate = true,
  backgroundColor = "#1a1a1a",
  onLoad,
  onError,
  onDownload,
  className,
}: ModelViewerProps) {
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [autoRotate, setAutoRotate] = React.useState(initialAutoRotate);
  const [isFullscreen, setIsFullscreen] = React.useState(false);
  const containerRef = React.useRef<HTMLDivElement>(null);

  const handleLoad = React.useCallback(() => {
    setIsLoading(false);
    setError(null);
    onLoad?.();
  }, [onLoad]);

  const handleError = React.useCallback(
    (err: Error) => {
      setIsLoading(false);
      setError(err.message || "Failed to load model");
      onError?.(err);
    },
    [onError]
  );

  const toggleFullscreen = React.useCallback(async () => {
    if (!containerRef.current) return;

    if (!document.fullscreenElement) {
      await containerRef.current.requestFullscreen();
      setIsFullscreen(true);
    } else {
      await document.exitFullscreen();
      setIsFullscreen(false);
    }
  }, []);

  // Listen for fullscreen changes
  React.useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener("fullscreenchange", handleFullscreenChange);
    return () => {
      document.removeEventListener("fullscreenchange", handleFullscreenChange);
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className={cn(
        "relative rounded-lg overflow-hidden bg-neutral-900",
        isFullscreen ? "fixed inset-0 z-50" : "aspect-square",
        className
      )}
    >
      {/* Loading State */}
      {isLoading && !error && (
        <div className="absolute inset-0 flex items-center justify-center bg-neutral-900 z-10">
          <div className="text-center">
            <Loader2 className="h-8 w-8 animate-spin text-axiom-500 mx-auto mb-2" />
            <p className="text-sm text-muted-foreground">Loading model...</p>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-neutral-900 z-10">
          <div className="text-center p-4">
            <AlertTriangle className="h-8 w-8 text-red-500 mx-auto mb-2" />
            <p className="text-sm text-red-400 mb-4">{error}</p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setError(null);
                setIsLoading(true);
              }}
            >
              <RotateCcw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </div>
        </div>
      )}

      {/* Three.js Canvas */}
      {!error && (
        <ThreeCanvas
          src={src}
          format={format}
          autoRotate={autoRotate}
          backgroundColor={backgroundColor}
          onLoad={handleLoad}
          onError={handleError}
        />
      )}

      {/* Controls Overlay */}
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex items-center gap-2 bg-black/60 backdrop-blur-sm rounded-full px-4 py-2">
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 text-white hover:bg-white/20"
          onClick={() => setAutoRotate(!autoRotate)}
          title={autoRotate ? "Stop rotation" : "Auto rotate"}
        >
          <RotateCcw
            className={cn("h-4 w-4", autoRotate && "animate-spin-slow")}
          />
        </Button>

        <div className="w-px h-4 bg-white/30" />

        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 text-white hover:bg-white/20"
          onClick={toggleFullscreen}
          title={isFullscreen ? "Exit fullscreen" : "Fullscreen"}
        >
          <Maximize2 className="h-4 w-4" />
        </Button>

        {onDownload && (
          <>
            <div className="w-px h-4 bg-white/30" />
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-white hover:bg-white/20"
              onClick={onDownload}
              title="Download model"
            >
              <Download className="h-4 w-4" />
            </Button>
          </>
        )}
      </div>

      {/* Keyboard Hints */}
      <div className="absolute top-4 right-4 text-xs text-white/50 space-y-1 select-none pointer-events-none">
        <p>Drag to rotate</p>
        <p>Scroll to zoom</p>
        <p>Shift+drag to pan</p>
      </div>
    </div>
  );
}

// =============================================================================
// Loading Skeleton
// =============================================================================

export function ModelViewerSkeleton() {
  return (
    <div className="aspect-square bg-neutral-900 rounded-lg flex items-center justify-center">
      <div className="text-center">
        <Box className="h-12 w-12 text-muted-foreground/30 mx-auto mb-4" />
        <Skeleton className="h-4 w-32 mx-auto" />
      </div>
    </div>
  );
}

// =============================================================================
// CSS for slow spin animation
// =============================================================================

// Add to globals.css:
// .animate-spin-slow {
//   animation: spin 3s linear infinite;
// }
