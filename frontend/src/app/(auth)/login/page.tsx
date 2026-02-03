// =============================================================================
// Axiom Design Engine - Login Page
// User authentication login form
// =============================================================================

"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2 } from "lucide-react";
import { useRedirectIfAuthenticated } from "@/hooks";
import { useAuthStore, useToast } from "@/store";
import { loginSchema, type LoginFormData } from "@/lib/validators";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function LoginPage() {
  const router = useRouter();
  const { login, isLoading, error, clearError } = useAuthStore();
  const { toast } = useToast();
  const { isLoading: isCheckingAuth } = useRedirectIfAuthenticated("/dashboard");
  const disableAuth =
    typeof process !== "undefined" &&
    process.env.NEXT_PUBLIC_DISABLE_AUTH === "true";

  React.useEffect(() => {
    if (disableAuth) {
      router.push("/dashboard");
    }
  }, [disableAuth, router]);

  const {
    register,
    handleSubmit,
    formState: { errors, isValid },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    mode: "onChange",
  });

  // Clear error on unmount
  React.useEffect(() => {
    return () => clearError();
  }, [clearError]);

  const onSubmit = async (data: LoginFormData) => {
    try {
      await login(data.email, data.password);
      toast({
        type: "success",
        title: "Welcome back!",
        message: "You have been successfully logged in.",
      });
      router.push("/dashboard");
    } catch (err) {
      // Error is handled by the store
    }
  };

  if (disableAuth || isCheckingAuth) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-axiom-500" />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 bg-gradient-to-b from-axiom-50 to-background dark:from-axiom-950 dark:to-background">
      {/* Logo */}
      <Link href="/" className="flex items-center gap-2 mb-8">
        <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-axiom-500 to-axiom-700 flex items-center justify-center">
          <span className="text-white font-bold text-xl">A</span>
        </div>
        <span className="font-semibold text-xl">Axiom Engine</span>
      </Link>

      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">Welcome Back</CardTitle>
          <CardDescription>
            Sign in to your account to continue
          </CardDescription>
        </CardHeader>

        <form onSubmit={handleSubmit(onSubmit)}>
          <CardContent className="space-y-4">
            {/* Global Error */}
            {error && (
              <div className="rounded-md bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 p-3">
                <p className="text-sm text-red-600 dark:text-red-400">
                  {error}
                </p>
              </div>
            )}

            {/* Email */}
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                autoComplete="email"
                error={errors.email?.message}
                {...register("email")}
              />
            </div>

            {/* Password */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="password">Password</Label>
                <Link
                  href="/forgot-password"
                  className="text-sm text-axiom-600 hover:text-axiom-700 dark:text-axiom-400"
                >
                  Forgot password?
                </Link>
              </div>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                autoComplete="current-password"
                error={errors.password?.message}
                {...register("password")}
              />
            </div>
          </CardContent>

          <CardFooter className="flex flex-col gap-4">
            <Button
              type="submit"
              className="w-full"
              disabled={!isValid || isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Signing in...
                </>
              ) : (
                "Sign In"
              )}
            </Button>

            <p className="text-sm text-center text-muted-foreground">
              Don&apos;t have an account?{" "}
              <Link
                href="/register"
                className="text-axiom-600 hover:text-axiom-700 dark:text-axiom-400 font-medium"
              >
                Create one
              </Link>
            </p>
          </CardFooter>
        </form>
      </Card>

      {/* Back to home */}
      <Link
        href="/"
        className="mt-8 text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        ← Back to home
      </Link>
    </div>
  );
}
