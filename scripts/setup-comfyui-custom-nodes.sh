#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Install required ComfyUI custom nodes into orchestration/custom_nodes
# =============================================================================

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CUSTOM_NODES_DIR="$ROOT_DIR/orchestration/custom_nodes"

mkdir -p "$CUSTOM_NODES_DIR"

clone_if_missing() {
  local repo_url="$1"
  local dir_name="$2"

  if [[ ! -d "$CUSTOM_NODES_DIR/$dir_name" ]]; then
    git clone "$repo_url" "$CUSTOM_NODES_DIR/$dir_name"
  fi
}

# Video helper suite (VHS_VideoCombine)
clone_if_missing "https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git" "ComfyUI-VideoHelperSuite"

# TripoSR node
clone_if_missing "https://github.com/44zon/ComfyUI-TripoSR.git" "ComfyUI-TripoSR"

printf "\nCustom nodes installed in %s\n" "$CUSTOM_NODES_DIR"
