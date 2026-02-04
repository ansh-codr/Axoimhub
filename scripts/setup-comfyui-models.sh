#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Prepare model folders for ComfyUI
# Place model files in the locations below.
# =============================================================================

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODELS_DIR="$ROOT_DIR/models"

mkdir -p "$MODELS_DIR/checkpoints" "$MODELS_DIR/vae" "$MODELS_DIR/loras" "$MODELS_DIR/clip_vision" "$MODELS_DIR/embeddings" "$MODELS_DIR/animatediff"

cat <<EOF
Model folders created at: $MODELS_DIR

Place the following model files:
- SDXL base: checkpoints/sd_xl_base_1.0.safetensors
- SVD XT: checkpoints/svd_xt_1_1.safetensors

TripoSR models are handled by the ComfyUI-TripoSR custom node.

If you keep models elsewhere, mount your models volume to /data/models in Docker.
EOF
