// =============================================================================
// Axiom Design Engine - Type Definitions
// Core types used throughout the frontend
// =============================================================================

// -----------------------------------------------------------------------------
// User Types
// -----------------------------------------------------------------------------

export interface User {
  id: string;
  email: string;
  username: string;
  full_name?: string;
  avatar_url?: string;
  role: UserRole;
  created_at: string;
  updated_at: string;
}

export type UserRole = "admin" | "user" | "viewer";

// -----------------------------------------------------------------------------
// Authentication Types
// -----------------------------------------------------------------------------

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  username: string;
  password: string;
  password_confirm: string;
  full_name?: string;
}

// -----------------------------------------------------------------------------
// Project Types
// -----------------------------------------------------------------------------

export interface Project {
  id: string;
  name: string;
  description?: string;
  owner_id: string;
  created_at: string;
  updated_at: string;
  asset_count?: number;
  job_count?: number;
}

export interface CreateProjectData {
  name: string;
  description?: string;
}

// -----------------------------------------------------------------------------
// Job Types
// -----------------------------------------------------------------------------

export type JobType = "image" | "video" | "model3d";

export type JobStatus =
  | "pending"
  | "queued"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

export interface Job {
  id: string;
  project_id: string;
  user_id: string;
  job_type: JobType;
  status: JobStatus;
  priority: number;
  prompt: string;
  parameters: JobParameters;
  progress?: number;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
  updated_at: string;
  assets?: Asset[];
}

export interface JobParameters {
  // Common parameters
  model?: string;
  seed?: number;
  
  // Image parameters
  width?: number;
  height?: number;
  steps?: number;
  cfg_scale?: number;
  sampler?: string;
  negative_prompt?: string;
  
  // Video parameters
  fps?: number;
  duration?: number;
  motion_bucket_id?: number;
  
  // 3D parameters
  format?: "glb" | "obj" | "fbx";
  texture_resolution?: number;
}

export interface CreateJobData {
  project_id: string;
  job_type: JobType;
  prompt: string;
  parameters?: JobParameters;
  priority?: number;
}

// -----------------------------------------------------------------------------
// Asset Types
// -----------------------------------------------------------------------------

export type AssetType = "image" | "video" | "model3d" | "texture";

export interface Asset {
  id: string;
  job_id: string;
  project_id: string;
  user_id: string;
  asset_type: AssetType;
  filename: string;
  file_size: number;
  mime_type: string;
  storage_path: string;
  url: string;
  thumbnail_url?: string;
  metadata?: AssetMetadata;
  created_at: string;
}

export interface AssetMetadata {
  width?: number;
  height?: number;
  duration?: number;
  fps?: number;
  format?: string;
  prompt?: string;
  seed?: number;
}

// -----------------------------------------------------------------------------
// API Response Types
// -----------------------------------------------------------------------------

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface ApiError {
  detail: string;
  code?: string;
  field?: string;
}

// -----------------------------------------------------------------------------
// UI State Types
// -----------------------------------------------------------------------------

export type ViewMode = "grid" | "list";

export type ThemeMode = "light" | "dark" | "system";

export interface ToastMessage {
  id: string;
  type: "success" | "error" | "warning" | "info";
  title: string;
  description?: string;
  duration?: number;
}
