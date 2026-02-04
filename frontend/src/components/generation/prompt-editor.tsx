// =============================================================================
// Axiom Design Engine - PromptEditor Component
// Main generation prompt editor with parameter controls
// =============================================================================

"use client";

import * as React from "react";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Image,
  Video,
  Box,
  Sparkles,
  Settings2,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { templatesApi } from "@/lib/api";
import { useToast } from "@/store";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import type { JobType } from "@/types";

// =============================================================================
// Schema Definitions
// =============================================================================

const baseSchema = z.object({
  prompt: z
    .string()
    .min(10, "Prompt must be at least 10 characters")
    .max(2000, "Prompt must be less than 2000 characters"),
  negative_prompt: z.string().max(1000).optional(),
  seed: z.number().int().min(-1).max(2147483647).optional(),
});

const imageSchema = baseSchema.extend({
  width: z.number().int().min(256).max(2048).default(768),
  height: z.number().int().min(256).max(2048).default(768),
  num_inference_steps: z.number().int().min(1).max(150).default(30),
  guidance_scale: z.number().min(1).max(30).default(7.5),
  model: z.enum(["sdxl"]).default("sdxl"),
  style: z.string().optional(),
});

const videoSchema = baseSchema.extend({
  width: z.number().int().min(256).max(1920).default(576),
  height: z.number().int().min(256).max(1080).default(320),
  num_frames: z.number().int().min(8).max(120).default(24),
  fps: z.number().int().min(1).max(60).default(24),
  motion_strength: z.number().min(0).max(1).default(0.5),
  model: z.enum(["svd"]).default("svd"),
});

const model3dSchema = baseSchema.extend({
  format: z.enum(["glb", "obj", "fbx"]).default("glb"),
  texture_resolution: z.number().int().min(256).max(4096).default(1024),
  geometry_detail: z.enum(["low", "medium", "high"]).default("medium"),
});

type ImageFormData = z.infer<typeof imageSchema>;
type VideoFormData = z.infer<typeof videoSchema>;
type Model3DFormData = z.infer<typeof model3dSchema>;
type FormData = ImageFormData | VideoFormData | Model3DFormData;

// =============================================================================
// Props Interface
// =============================================================================

export interface PromptEditorProps {
  projectId: string;
  onGenerate: (
    jobType: JobType,
    prompt: string,
    parameters: Record<string, unknown>
  ) => Promise<void>;
  isGenerating?: boolean;
  defaultJobType?: JobType;
  className?: string;
}

// =============================================================================
// Component
// =============================================================================

export function PromptEditor({
  projectId,
  onGenerate,
  isGenerating = false,
  defaultJobType = "image",
  className,
}: PromptEditorProps) {
  const [jobType, setJobType] = React.useState<JobType>(defaultJobType);
  const [showAdvanced, setShowAdvanced] = React.useState(false);
  const [isEnhancing, setIsEnhancing] = React.useState(false);
  const toast = useToast();

  // Select schema based on job type
  const schema = React.useMemo(() => {
    switch (jobType) {
      case "video":
        return videoSchema;
      case "model3d":
        return model3dSchema;
      default:
        return imageSchema;
    }
  }, [jobType]);

  const {
    register,
    handleSubmit,
    control,
    reset,
    getValues,
    setValue,
    formState: { errors, isValid },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    mode: "onChange",
    defaultValues: {
      prompt: "",
      negative_prompt: "",
      seed: -1,
    },
  });

  // Reset form when job type changes
  React.useEffect(() => {
    reset();
  }, [jobType, reset]);

  const onSubmit = async (data: FormData) => {
    const { prompt, ...parameters } = data;
    await onGenerate(jobType, prompt, parameters);
  };

  const handleEnhancePrompt = async () => {
    const currentPrompt = getValues("prompt")?.trim();
    if (!currentPrompt) {
      toast.warning(
        "Prompt required",
        "Enter a prompt before enhancing."
      );
      return;
    }

    setIsEnhancing(true);
    try {
      const response = await templatesApi.enhance(currentPrompt, jobType);
      setValue("prompt", response.enhanced_prompt, { shouldValidate: true });

      const currentNegative = getValues("negative_prompt")?.trim();
      if (!currentNegative && response.default_negative_prompt) {
        setValue("negative_prompt", response.default_negative_prompt, {
          shouldValidate: true,
        });
      }

      toast.success(
        "Prompt enhanced",
        "Your prompt was refined for better results."
      );
    } catch (error) {
      toast.error(
        "Enhancement failed",
        "Please try again."
      );
    } finally {
      setIsEnhancing(false);
    }
  };

  return (
    <div
      className={cn(
        "rounded-lg border bg-card p-6 shadow-sm",
        className
      )}
    >
      {/* Job Type Selector */}
      <Tabs
        value={jobType}
        onValueChange={(v) => setJobType(v as JobType)}
        className="mb-6"
      >
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="image" className="gap-2">
            <Image className="h-4 w-4" />
            Image
          </TabsTrigger>
          <TabsTrigger value="video" className="gap-2">
            <Video className="h-4 w-4" />
            Video
          </TabsTrigger>
          <TabsTrigger value="model3d" className="gap-2">
            <Box className="h-4 w-4" />
            3D Model
          </TabsTrigger>
        </TabsList>
      </Tabs>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Main Prompt */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label htmlFor="prompt">Prompt</Label>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleEnhancePrompt}
              isLoading={isEnhancing}
            >
              Enhance
            </Button>
          </div>
          <Textarea
            id="prompt"
            placeholder={getPlaceholder(jobType)}
            className="min-h-[120px] resize-y"
            error={errors.prompt?.message}
            {...register("prompt")}
          />
          <p className="text-xs text-muted-foreground">
            Describe what you want to generate in detail. Be specific about
            style, colors, composition, and mood.
          </p>
        </div>

        {/* Negative Prompt */}
        <div className="space-y-2">
          <Label htmlFor="negative_prompt">Negative Prompt (optional)</Label>
          <Textarea
            id="negative_prompt"
            placeholder="blur, low quality, distorted, watermark..."
            className="min-h-[60px] resize-y"
            error={errors.negative_prompt?.message}
            {...register("negative_prompt")}
          />
        </div>

        {/* Advanced Settings Toggle */}
        <button
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex items-center gap-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
        >
          <Settings2 className="h-4 w-4" />
          Advanced Settings
          {showAdvanced ? (
            <ChevronUp className="h-4 w-4" />
          ) : (
            <ChevronDown className="h-4 w-4" />
          )}
        </button>

        {/* Advanced Settings Panel */}
        {showAdvanced && (
          <div className="rounded-lg border bg-muted/30 p-4 space-y-4">
            {jobType === "image" && (
              <ImageAdvancedSettings
                register={register}
                control={control}
                errors={errors}
              />
            )}
            {jobType === "video" && (
              <VideoAdvancedSettings
                register={register}
                control={control}
                errors={errors}
              />
            )}
            {jobType === "model3d" && (
              <Model3DAdvancedSettings
                control={control}
                errors={errors}
              />
            )}

            {/* Common: Seed */}
            <div className="space-y-2">
              <Label htmlFor="seed">Seed</Label>
              <Input
                id="seed"
                type="number"
                placeholder="-1 (random)"
                error={errors.seed?.message}
                {...register("seed", { valueAsNumber: true })}
              />
              <p className="text-xs text-muted-foreground">
                Use -1 for random seed, or specify a value for reproducible results.
              </p>
            </div>
          </div>
        )}

        {/* Generate Button */}
        <Button
          type="submit"
          size="lg"
          className="w-full"
          disabled={!isValid || isGenerating}
          isLoading={isGenerating}
        >
          <Sparkles className="mr-2 h-5 w-5" />
          Generate {getJobTypeLabel(jobType)}
        </Button>
      </form>
    </div>
  );
}

// =============================================================================
// Advanced Settings Sub-components
// =============================================================================

function ImageAdvancedSettings({
  register,
  control,
  errors,
}: {
  register: any;
  control: any;
  errors: any;
}) {
  return (
    <>
      <div className="space-y-2">
        <Label>Model</Label>
        <Controller
          name="model"
          control={control}
          render={({ field }) => (
            <Select onValueChange={field.onChange} value={field.value}>
              <SelectTrigger>
                <SelectValue placeholder="SDXL" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="sdxl">SDXL (Recommended)</SelectItem>
              </SelectContent>
            </Select>
          )}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="width">Width</Label>
          <Input
            id="width"
            type="number"
            step={64}
            error={errors.width?.message}
            {...register("width", { valueAsNumber: true })}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="height">Height</Label>
          <Input
            id="height"
            type="number"
            step={64}
            error={errors.height?.message}
            {...register("height", { valueAsNumber: true })}
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="num_inference_steps">Steps</Label>
          <Input
            id="num_inference_steps"
            type="number"
            error={errors.num_inference_steps?.message}
            {...register("num_inference_steps", { valueAsNumber: true })}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="guidance_scale">Guidance Scale</Label>
          <Input
            id="guidance_scale"
            type="number"
            step={0.5}
            error={errors.guidance_scale?.message}
            {...register("guidance_scale", { valueAsNumber: true })}
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label>Style Preset</Label>
        <Controller
          name="style"
          control={control}
          render={({ field }) => (
            <Select onValueChange={field.onChange} value={field.value}>
              <SelectTrigger>
                <SelectValue placeholder="None" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">None</SelectItem>
                <SelectItem value="photorealistic">Photorealistic</SelectItem>
                <SelectItem value="digital-art">Digital Art</SelectItem>
                <SelectItem value="anime">Anime</SelectItem>
                <SelectItem value="cinematic">Cinematic</SelectItem>
                <SelectItem value="fantasy">Fantasy</SelectItem>
                <SelectItem value="minimalist">Minimalist</SelectItem>
              </SelectContent>
            </Select>
          )}
        />
      </div>
    </>
  );
}

function VideoAdvancedSettings({
  register,
  control,
  errors,
}: {
  register: any;
  control: any;
  errors: any;
}) {
  return (
    <>
      <div className="space-y-2">
        <Label>Model</Label>
        <Controller
          name="model"
          control={control}
          render={({ field }) => (
            <Select onValueChange={field.onChange} value={field.value}>
              <SelectTrigger>
                <SelectValue placeholder="SVD" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="svd">SVD (Recommended)</SelectItem>
              </SelectContent>
            </Select>
          )}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="width">Width</Label>
          <Input
            id="width"
            type="number"
            step={64}
            error={errors.width?.message}
            {...register("width", { valueAsNumber: true })}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="height">Height</Label>
          <Input
            id="height"
            type="number"
            step={64}
            error={errors.height?.message}
            {...register("height", { valueAsNumber: true })}
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="num_frames">Frames</Label>
          <Input
            id="num_frames"
            type="number"
            error={errors.num_frames?.message}
            {...register("num_frames", { valueAsNumber: true })}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="fps">FPS</Label>
          <Input
            id="fps"
            type="number"
            error={errors.fps?.message}
            {...register("fps", { valueAsNumber: true })}
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="motion_strength">Motion Strength (0-1)</Label>
        <Input
          id="motion_strength"
          type="number"
          step={0.1}
          min={0}
          max={1}
          error={errors.motion_strength?.message}
          {...register("motion_strength", { valueAsNumber: true })}
        />
      </div>
    </>
  );
}

function Model3DAdvancedSettings({
  control,
  errors,
}: {
  control: any;
  errors: any;
}) {
  return (
    <>
      <div className="space-y-2">
        <Label>Output Format</Label>
        <Controller
          name="format"
          control={control}
          render={({ field }) => (
            <Select onValueChange={field.onChange} value={field.value}>
              <SelectTrigger>
                <SelectValue placeholder="GLB" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="glb">GLB (Recommended)</SelectItem>
                <SelectItem value="obj">OBJ</SelectItem>
                <SelectItem value="fbx">FBX</SelectItem>
              </SelectContent>
            </Select>
          )}
        />
      </div>

      <div className="space-y-2">
        <Label>Geometry Detail</Label>
        <Controller
          name="geometry_detail"
          control={control}
          render={({ field }) => (
            <Select onValueChange={field.onChange} value={field.value}>
              <SelectTrigger>
                <SelectValue placeholder="Medium" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="low">Low (Faster)</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="high">High (Slower)</SelectItem>
              </SelectContent>
            </Select>
          )}
        />
      </div>

      <div className="space-y-2">
        <Label>Texture Resolution</Label>
        <Controller
          name="texture_resolution"
          control={control}
          render={({ field }) => (
            <Select
              onValueChange={(v) => field.onChange(parseInt(v))}
              value={field.value?.toString()}
            >
              <SelectTrigger>
                <SelectValue placeholder="1024" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="256">256px</SelectItem>
                <SelectItem value="512">512px</SelectItem>
                <SelectItem value="1024">1024px</SelectItem>
                <SelectItem value="2048">2048px</SelectItem>
                <SelectItem value="4096">4096px</SelectItem>
              </SelectContent>
            </Select>
          )}
        />
      </div>
    </>
  );
}

// =============================================================================
// Helpers
// =============================================================================

function getPlaceholder(jobType: JobType): string {
  switch (jobType) {
    case "video":
      return "A futuristic cityscape at sunset, flying cars passing by, neon lights reflecting on wet streets, cinematic camera movement...";
    case "model3d":
      return "A stylized low-poly treasure chest with gold coins and jewels, wooden texture with metal hinges, game-ready asset...";
    default:
      return "A serene Japanese garden with cherry blossoms, stone path leading to a traditional tea house, soft morning light, detailed watercolor style...";
  }
}

function getJobTypeLabel(jobType: JobType): string {
  switch (jobType) {
    case "video":
      return "Video";
    case "model3d":
      return "3D Model";
    default:
      return "Image";
  }
}

// =============================================================================
// Loading Skeleton
// =============================================================================

export function PromptEditorSkeleton() {
  return (
    <div className="rounded-lg border bg-card p-6 shadow-sm space-y-6">
      <Skeleton className="h-10 w-full" />
      <div className="space-y-2">
        <Skeleton className="h-4 w-16" />
        <Skeleton className="h-32 w-full" />
      </div>
      <div className="space-y-2">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-16 w-full" />
      </div>
      <Skeleton className="h-12 w-full" />
    </div>
  );
}
