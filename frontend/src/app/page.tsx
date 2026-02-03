// =============================================================================
// Axiom Design Engine - Landing Page
// Public homepage with hero and features
// =============================================================================

import Link from "next/link";
import { ArrowRight, Image, Video, Box, Sparkles, Zap, Shield } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Header } from "@/components/layout/header";
import { Footer } from "@/components/layout/footer";

// =============================================================================
// Features Data
// =============================================================================

const features = [
  {
    icon: Image,
    title: "AI Image Generation",
    description:
      "Generate stunning UI mockups, icons, illustrations, and design assets with state-of-the-art diffusion models.",
  },
  {
    icon: Video,
    title: "Video Creation",
    description:
      "Create short animated videos, UI transitions, and motion graphics powered by video diffusion technology.",
  },
  {
    icon: Box,
    title: "3D Asset Generation",
    description:
      "Generate 3D models, textures, and environments ready for games, AR/VR, and product visualization.",
  },
  {
    icon: Sparkles,
    title: "ComfyUI Integration",
    description:
      "Built on the powerful ComfyUI backend with customizable workflows and extensible node systems.",
  },
  {
    icon: Zap,
    title: "High Performance",
    description:
      "Optimized for speed with GPU acceleration, queue management, and intelligent caching.",
  },
  {
    icon: Shield,
    title: "Self-Hosted & Private",
    description:
      "Run on your own infrastructure. Your data stays yours. No cloud dependencies required.",
  },
];

// =============================================================================
// Page Component
// =============================================================================

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />

      <main className="flex-1">
        {/* Hero Section */}
        <section className="relative overflow-hidden bg-gradient-to-b from-axiom-50 to-background dark:from-axiom-950 dark:to-background">
          <div className="absolute inset-0 bg-grid-pattern opacity-5" />
          <div className="container relative px-4 py-24 md:py-32 lg:py-40">
            <div className="mx-auto max-w-3xl text-center">
              <div className="mb-6 inline-flex items-center rounded-full border bg-background/80 backdrop-blur px-4 py-1.5 text-sm">
                <Sparkles className="mr-2 h-4 w-4 text-axiom-500" />
                <span>Open Source AI Design Platform</span>
              </div>

              <h1 className="text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl lg:text-7xl">
                Create Stunning{" "}
                <span className="gradient-text">Design Assets</span> with AI
              </h1>

              <p className="mt-6 text-lg text-muted-foreground md:text-xl">
                Axiom Design Engine is a self-hosted AI platform for generating
                UI/UX-focused images, videos, and 3D assets. Powered by ComfyUI
                and modern diffusion models.
              </p>

              <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
                <Button size="lg" asChild>
                  <Link href="/register">
                    Get Started Free
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Link>
                </Button>
                <Button size="lg" variant="outline" asChild>
                  <Link href="/docs">View Documentation</Link>
                </Button>
              </div>

              <p className="mt-6 text-sm text-muted-foreground">
                No credit card required • Self-host or cloud • MIT License
              </p>
            </div>
          </div>

          {/* Hero Image/Demo */}
          <div className="container px-4 pb-16">
            <div className="relative mx-auto max-w-5xl">
              <div className="rounded-xl border bg-card shadow-2xl overflow-hidden">
                <div className="aspect-video bg-gradient-to-br from-axiom-100 to-axiom-200 dark:from-axiom-900 dark:to-axiom-800 flex items-center justify-center">
                  <div className="text-center p-8">
                    <div className="inline-flex items-center justify-center h-16 w-16 rounded-full bg-axiom-500/20 mb-4">
                      <Sparkles className="h-8 w-8 text-axiom-500" />
                    </div>
                    <p className="text-lg font-medium">
                      Interactive Demo Coming Soon
                    </p>
                    <p className="text-sm text-muted-foreground mt-2">
                      Generate images, videos, and 3D assets in real-time
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="py-24 md:py-32">
          <div className="container px-4">
            <div className="mx-auto max-w-2xl text-center mb-16">
              <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
                Everything You Need for AI Design
              </h2>
              <p className="mt-4 text-lg text-muted-foreground">
                A complete platform for generating, managing, and deploying
                AI-created design assets.
              </p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
              {features.map((feature) => (
                <div
                  key={feature.title}
                  className="rounded-xl border bg-card p-6 shadow-sm hover:shadow-md transition-shadow"
                >
                  <div className="inline-flex items-center justify-center h-12 w-12 rounded-lg bg-axiom-100 dark:bg-axiom-900 mb-4">
                    <feature.icon className="h-6 w-6 text-axiom-600 dark:text-axiom-400" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                  <p className="text-muted-foreground">{feature.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-24 md:py-32 bg-axiom-600 dark:bg-axiom-900">
          <div className="container px-4">
            <div className="mx-auto max-w-2xl text-center">
              <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
                Ready to Transform Your Design Workflow?
              </h2>
              <p className="mt-4 text-lg text-axiom-100">
                Start generating AI-powered design assets in minutes. Self-host
                on your own infrastructure or get started with our cloud
                offering.
              </p>
              <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
                <Button
                  size="lg"
                  variant="secondary"
                  className="bg-white text-axiom-600 hover:bg-axiom-50"
                  asChild
                >
                  <Link href="/register">
                    Start Free Trial
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Link>
                </Button>
                <Button
                  size="lg"
                  variant="outline"
                  className="border-white text-white hover:bg-white/10"
                  asChild
                >
                  <Link href="https://github.com/axiom-engine">
                    View on GitHub
                  </Link>
                </Button>
              </div>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
