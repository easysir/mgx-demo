#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKEND_DIR="${REPO_ROOT}/apps/backend"
VENV_PATH="${MGX_BACKEND_VENV:-$HOME/venvs/mgx}"

if [[ ! -d "$VENV_PATH" ]]; then
  echo "Backend virtualenv not found at $VENV_PATH. Set MGX_BACKEND_VENV or create the venv." >&2
  exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "'uv' command not found. Please install Astral uv (https://github.com/astral-sh/uv)." >&2
  exit 1
fi

source "$VENV_PATH/bin/activate"
cd "$BACKEND_DIR"

echo "==> Syncing backend Python dependencies via uv --active (venv: $VENV_PATH)"
uv sync --active "$@"
