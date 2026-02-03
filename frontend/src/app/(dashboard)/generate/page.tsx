// =============================================================================
// Axiom Design Engine - Generate Index Page
// Redirect to dashboard or show generation options
// =============================================================================

"use client";

import Link from "next/link";
import { Image, Video, Box } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";

const generationTypes = [
  {
    href: "/generate/image",
    icon: Image,
    title: "Image Generation",
    description: "Create stunning UI/UX images, icons, and illustrations",
    features: ["Custom dimensions", "Style presets", "High resolution output"],
  },
  {
    href: "/generate/video",
    icon: Video,
    title: "Video Generation",
    description: "Generate animated videos and motion graphics",
    features: ["Duration control", "Frame rate options", "Multiple formats"],
  },
  {
    href: "/generate/3d",
    icon: Box,
    title: "3D Model Generation",
    description: "Create 3D assets for your design projects",
    features: ["GLTF/GLB export", "Interactive preview", "Material options"],
  },
];

export default function GenerateIndexPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Generate</h1>
        <p className="text-muted-foreground">
          Choose a generation type to create AI-powered assets
        </p>
      </div>

      {/* Generation Options */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {generationTypes.map((type) => (
          <Link key={type.href} href={type.href}>
            <Card className="h-full transition-colors hover:border-axiom-500 hover:bg-axiom-50/50 dark:hover:bg-axiom-950/30">
              <CardHeader>
                <div className="mb-2 inline-flex h-10 w-10 items-center justify-center rounded-lg bg-axiom-100 dark:bg-axiom-900">
                  <type.icon className="h-5 w-5 text-axiom-600 dark:text-axiom-400" />
                </div>
                <CardTitle>{type.title}</CardTitle>
                <CardDescription>{type.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-1 text-sm text-muted-foreground">
                  {type.features.map((feature) => (
                    <li key={feature} className="flex items-center">
                      <span className="mr-2 h-1 w-1 rounded-full bg-axiom-500" />
                      {feature}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
