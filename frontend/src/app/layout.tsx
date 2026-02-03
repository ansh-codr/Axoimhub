// =============================================================================
// Axiom Design Engine - Root Layout
// App-wide layout with providers
// =============================================================================

import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "@/styles/globals.css";
import { Providers } from "@/components/providers";
import { Toaster } from "@/components/ui/toaster";

// =============================================================================
// Font Configuration
// =============================================================================

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
});

// =============================================================================
// Metadata
// =============================================================================

export const metadata: Metadata = {
  title: {
    default: "Axiom Design Engine",
    template: "%s | Axiom Design Engine",
  },
  description:
    "Self-hosted AI platform for generating UI/UX-focused images, videos, and 3D assets.",
  keywords: [
    "AI",
    "design",
    "image generation",
    "video generation",
    "3D generation",
    "UI/UX",
    "ComfyUI",
  ],
  authors: [{ name: "Axiom Team" }],
  creator: "Axiom Team",
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://axiom.design",
    siteName: "Axiom Design Engine",
    title: "Axiom Design Engine",
    description:
      "Self-hosted AI platform for generating UI/UX-focused images, videos, and 3D assets.",
  },
  twitter: {
    card: "summary_large_image",
    title: "Axiom Design Engine",
    description:
      "Self-hosted AI platform for generating UI/UX-focused images, videos, and 3D assets.",
    creator: "@axiomengine",
  },
  manifest: "/manifest.json",
  icons: {
    icon: "/favicon.ico",
    shortcut: "/favicon-16x16.png",
    apple: "/apple-touch-icon.png",
  },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#0a0a0a" },
  ],
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
};

// =============================================================================
// Layout Component
// =============================================================================

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${inter.variable} font-sans antialiased`}
        suppressHydrationWarning
      >
        <Providers>
          {children}
          <Toaster />
        </Providers>
      </body>
    </html>
  );
}
