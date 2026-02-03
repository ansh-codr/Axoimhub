// =============================================================================
// Axiom Design Engine - ModelViewerCanvas Component
// Three.js Canvas implementation with React Three Fiber
// =============================================================================

"use client";

import * as React from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { OrbitControls, Environment, Center, useGLTF, useProgress, Html } from "@react-three/drei";
import * as THREE from "three";

// =============================================================================
// Props Interface
// =============================================================================

export interface ModelViewerCanvasProps {
  src: string;
  format?: "glb" | "gltf" | "obj" | "fbx";
  autoRotate?: boolean;
  backgroundColor?: string;
  onLoad?: () => void;
  onError?: (error: Error) => void;
}

// =============================================================================
// Main Canvas Component
// =============================================================================

export function ModelViewerCanvas({
  src,
  format = "glb",
  autoRotate = true,
  backgroundColor = "#1a1a1a",
  onLoad,
  onError,
}: ModelViewerCanvasProps) {
  return (
    <Canvas
      camera={{ position: [0, 0, 5], fov: 50 }}
      style={{ background: backgroundColor }}
      gl={{
        antialias: true,
        toneMapping: THREE.ACESFilmicToneMapping,
        toneMappingExposure: 1,
      }}
      onCreated={({ gl }) => {
        gl.setClearColor(backgroundColor);
      }}
    >
      {/* Lighting */}
      <ambientLight intensity={0.5} />
      <directionalLight position={[10, 10, 5]} intensity={1} castShadow />
      <directionalLight position={[-10, -10, -5]} intensity={0.5} />

      {/* Environment for reflections */}
      <Environment preset="studio" />

      {/* Model */}
      <React.Suspense fallback={<LoadingIndicator />}>
        <Center>
          <Model
            src={src}
            format={format}
            onLoad={onLoad}
            onError={onError}
          />
        </Center>
      </React.Suspense>

      {/* Controls */}
      <OrbitControls
        autoRotate={autoRotate}
        autoRotateSpeed={2}
        enablePan={true}
        enableZoom={true}
        enableRotate={true}
        minDistance={1}
        maxDistance={100}
        makeDefault
      />

      {/* Grid Helper (optional) */}
      <gridHelper args={[10, 10, "#333333", "#222222"]} position={[0, -1, 0]} />
    </Canvas>
  );
}

// =============================================================================
// Model Component
// =============================================================================

interface ModelProps {
  src: string;
  format: string;
  onLoad?: () => void;
  onError?: (error: Error) => void;
}

function Model({ src, format, onLoad, onError }: ModelProps) {
  const { scene } = useGLTF(src, true, true, (loader) => {
    loader.manager.onError = (url) => {
      onError?.(new Error(`Failed to load: ${url}`));
    };
  });

  React.useEffect(() => {
    if (scene) {
      // Auto-scale model to fit view
      const box = new THREE.Box3().setFromObject(scene);
      const size = box.getSize(new THREE.Vector3());
      const maxDim = Math.max(size.x, size.y, size.z);
      const scale = 2 / maxDim;
      scene.scale.setScalar(scale);

      // Center the model
      const center = box.getCenter(new THREE.Vector3());
      scene.position.sub(center.multiplyScalar(scale));

      onLoad?.();
    }
  }, [scene, onLoad]);

  return <primitive object={scene} />;
}

// =============================================================================
// Loading Indicator
// =============================================================================

function LoadingIndicator() {
  const { progress } = useProgress();

  return (
    <Html center>
      <div className="text-center text-white">
        <div className="w-32 h-1 bg-white/20 rounded-full overflow-hidden">
          <div
            className="h-full bg-axiom-500 transition-all duration-200"
            style={{ width: `${progress}%` }}
          />
        </div>
        <p className="mt-2 text-xs text-white/60">{Math.round(progress)}%</p>
      </div>
    </Html>
  );
}

// =============================================================================
// Preload helper
// =============================================================================

useGLTF.preload = (url: string) => {
  useGLTF(url);
};
