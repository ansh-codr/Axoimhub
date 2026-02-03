// =============================================================================
// Axiom Design Engine - Register Page
// User registration form
// =============================================================================

"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2, Check } from "lucide-react";
import { useRedirectIfAuthenticated } from "@/hooks";
import { useAuthStore, useToast } from "@/store";
import { registerSchema, type RegisterFormData } from "@/lib/validators";
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

// =============================================================================
// Password Requirements
// =============================================================================

const passwordRequirements = [
  { regex: /.{10,}/, label: "At least 10 characters" },
  { regex: /[A-Z]/, label: "One uppercase letter" },
  { regex: /[a-z]/, label: "One lowercase letter" },
  { regex: /[0-9]/, label: "One number" },
  { regex: /[!@#$%^&*()_+\-=[\]{}|;:,.<>?]/, label: "One special character" },
];

export default function RegisterPage() {
  const router = useRouter();
  const { register: registerUser, isLoading, error, clearError } = useAuthStore();
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
    watch,
    formState: { errors, isValid },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    mode: "onChange",
  });

  const password = watch("password", "");

  // Clear error on unmount
  React.useEffect(() => {
    return () => clearError();
  }, [clearError]);

  const onSubmit = async (data: RegisterFormData) => {
    try {
      await registerUser(
        data.email,
        data.username,
        data.password,
        data.confirmPassword,
        data.fullName
      );
      toast({
        type: "success",
        title: "Account created!",
        message: "Welcome to Axiom Design Engine.",
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
          <CardTitle className="text-2xl">Create Your Account</CardTitle>
          <CardDescription>
            Get started with Axiom Design Engine
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

            {/* Username */}
            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                type="text"
                placeholder="johndoe"
                autoComplete="username"
                error={errors.username?.message}
                {...register("username")}
              />
            </div>

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
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                autoComplete="new-password"
                error={errors.password?.message}
                {...register("password")}
              />
              {/* Password Requirements */}
              <div className="space-y-1 pt-2">
                {passwordRequirements.map((req) => {
                  const met = req.regex.test(password);
                  return (
                    <div
                      key={req.label}
                      className={`flex items-center gap-2 text-xs ${
                        met ? "text-green-600" : "text-muted-foreground"
                      }`}
                    >
                      <Check
                        className={`h-3 w-3 ${
                          met ? "opacity-100" : "opacity-30"
                        }`}
                      />
                      {req.label}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Confirm Password */}
            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Confirm Password</Label>
              <Input
                id="confirmPassword"
                type="password"
                placeholder="••••••••"
                autoComplete="new-password"
                error={errors.confirmPassword?.message}
                {...register("confirmPassword")}
              />
            </div>

            {/* Terms */}
            <p className="text-xs text-muted-foreground">
              By creating an account, you agree to our{" "}
              <Link
                href="/terms"
                className="text-axiom-600 hover:underline"
              >
                Terms of Service
              </Link>{" "}
              and{" "}
              <Link
                href="/privacy"
                className="text-axiom-600 hover:underline"
              >
                Privacy Policy
              </Link>
              .
            </p>
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
                  Creating account...
                </>
              ) : (
                "Create Account"
              )}
            </Button>

            <p className="text-sm text-center text-muted-foreground">
              Already have an account?{" "}
              <Link
                href="/login"
                className="text-axiom-600 hover:text-axiom-700 dark:text-axiom-400 font-medium"
              >
                Sign in
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
