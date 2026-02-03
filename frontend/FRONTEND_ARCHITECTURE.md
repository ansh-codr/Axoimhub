# Axiom Design Engine - Frontend Architecture

## Component 5: Frontend Component Architecture

This document outlines the frontend architecture for the Axiom Design Engine, a self-hosted AI platform for generating UI/UX-focused images, videos, and 3D assets.

## Technology Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript (strict mode)
- **State Management**: Zustand with persist middleware
- **Styling**: Tailwind CSS with CSS variables
- **UI Components**: Radix UI primitives
- **Animations**: Framer Motion
- **3D Rendering**: React Three Fiber + drei
- **Forms**: React Hook Form + Zod
- **HTTP Client**: Axios with interceptors
- **Icons**: Lucide React

## Directory Structure

```
frontend/src/
├── app/                    # Next.js App Router
│   ├── (auth)/             # Auth route group (login, register)
│   ├── (dashboard)/        # Protected dashboard routes
│   │   ├── dashboard/      # Main dashboard
│   │   ├── projects/       # Project management
│   │   ├── assets/         # Asset browser
│   │   ├── generate/       # Generation pages (image/video/3d)
│   │   ├── history/        # Job history
│   │   └── settings/       # User settings
│   ├── layout.tsx          # Root layout
│   ├── page.tsx            # Landing page
│   ├── loading.tsx         # Global loading state
│   ├── not-found.tsx       # 404 page
│   └── global-error.tsx    # Error boundary
│
├── components/
│   ├── ui/                 # Base UI components
│   │   ├── button.tsx      # Variants: default, destructive, outline, secondary, ghost, link
│   │   ├── input.tsx       # With error state
│   │   ├── textarea.tsx    # Multi-line input
│   │   ├── label.tsx       # Form labels
│   │   ├── card.tsx        # Card layouts
│   │   ├── dialog.tsx      # Modal dialogs
│   │   ├── select.tsx      # Dropdown select
│   │   ├── tabs.tsx        # Tab navigation
│   │   ├── progress.tsx    # Progress indicator
│   │   ├── badge.tsx       # Status badges
│   │   ├── avatar.tsx      # User avatars
│   │   ├── skeleton.tsx    # Loading placeholders
│   │   ├── toast.tsx       # Toast notifications
│   │   ├── toaster.tsx     # Toast container
│   │   └── dropdown-menu.tsx # Context menus
│   │
│   ├── generation/         # Generation-specific components
│   │   ├── prompt-editor.tsx    # Prompt input with settings
│   │   ├── job-status-panel.tsx # Job monitoring
│   │   └── asset-gallery.tsx    # Asset grid/list view
│   │
│   ├── three/              # 3D visualization
│   │   ├── model-viewer.tsx        # Viewer wrapper
│   │   └── model-viewer-canvas.tsx # R3F canvas
│   │
│   ├── layout/             # Layout components
│   │   ├── header.tsx      # App header
│   │   ├── sidebar.tsx     # Navigation sidebar
│   │   └── footer.tsx      # App footer
│   │
│   ├── providers.tsx       # Context providers
│   └── index.ts            # Component exports
│
├── hooks/                  # Custom React hooks
│   ├── use-auth.ts         # Authentication hooks
│   ├── use-jobs.ts         # Job management hooks
│   ├── use-assets.ts       # Asset management hooks
│   └── index.ts            # Hook exports
│
├── store/                  # Zustand stores
│   ├── auth-store.ts       # User authentication state
│   ├── jobs-store.ts       # Job management state
│   ├── assets-store.ts     # Asset list state
│   ├── ui-store.ts         # UI state (theme, toasts, modals)
│   └── index.ts            # Store exports
│
├── lib/                    # Utilities and configurations
│   ├── api-client.ts       # Axios instance with interceptors
│   ├── api.ts              # API service methods
│   ├── validators.ts       # Zod schemas
│   └── utils.ts            # Helper functions
│
├── types/                  # TypeScript definitions
│   └── index.ts            # Shared types
│
└── styles/
    └── globals.css         # Global styles with CSS variables
```

## Key Components

### PromptEditor
Multi-tab form for generating different asset types:
- Image generation with dimension/style presets
- Video generation with duration/frame rate controls
- 3D model generation with format options
- Advanced settings panel

### JobStatusPanel
Real-time job monitoring:
- Status indicators (pending, queued, running, completed, failed, cancelled)
- Progress visualization
- Timing information
- Cancel/Retry actions

### AssetGallery
Asset browser with multiple views:
- Grid and list view modes
- Type filtering (all, image, video, 3D)
- Search functionality
- Preview modal with metadata
- Download/delete actions

### ModelViewer
Interactive 3D model preview:
- GLTF/GLB support via React Three Fiber
- Orbit controls for rotation/zoom
- Auto-rotation toggle
- Fullscreen mode
- Loading/error states

## State Management

### AuthStore
```typescript
interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  error: string | null;
}
```

### JobsStore
```typescript
interface JobsState {
  jobs: Job[];
  currentJob: Job | null;
  isLoading: boolean;
  error: string | null;
  pollingInterval: number | null;
}
```

### AssetsStore
```typescript
interface AssetsState {
  assets: Asset[];
  viewMode: 'grid' | 'list';
  filterType: AssetType | 'all';
  searchQuery: string;
}
```

### UIStore
```typescript
interface UIState {
  theme: 'light' | 'dark' | 'system';
  sidebarOpen: boolean;
  toasts: Toast[];
  modals: Record<string, boolean>;
}
```

## API Integration

The frontend communicates with the backend via REST API:

- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `GET /api/auth/profile` - Get current user
- `POST /api/jobs` - Create generation job
- `GET /api/jobs` - List jobs with filters
- `GET /api/jobs/:id` - Get job details
- `DELETE /api/jobs/:id` - Cancel job
- `POST /api/jobs/:id/retry` - Retry failed job
- `GET /api/assets` - List assets
- `GET /api/assets/:id` - Get asset details
- `GET /api/assets/:id/download` - Download asset
- `DELETE /api/assets/:id` - Delete asset

## Theming

The app uses CSS variables for theming, supporting light, dark, and system modes:

```css
:root {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  --primary: 199 89% 48%; /* Axiom blue */
  /* ... */
}

.dark {
  --background: 222.2 84% 4.9%;
  --foreground: 210 40% 98%;
  /* ... */
}
```

## Getting Started

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

## Environment Variables

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```
