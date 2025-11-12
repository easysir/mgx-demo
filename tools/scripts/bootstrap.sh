#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "==> Installing Node dependencies via pnpm"
(cd "$ROOT_DIR" && pnpm install)

PY_ENV="${HOME}/venvs/mgx"
echo "==> Ensuring Python virtual environment at ${PY_ENV}"
mkdir -p "$(dirname "$PY_ENV")"
if [ ! -d "$PY_ENV" ]; then
  if command -v python3 >/dev/null 2>&1; then
    python3 -m venv "$PY_ENV"
  else
    echo "python3 not found; cannot create virtual environment." >&2
    exit 1
  fi
fi

echo "==> Installing backend dependencies into ${PY_ENV}"
if command -v uv >/dev/null 2>&1; then
  (cd "$ROOT_DIR/apps/backend" && UV_PROJECT_ENVIRONMENT="$PY_ENV" uv sync)
else
  "$PY_ENV/bin/python" -m pip install --upgrade pip
  (cd "$ROOT_DIR/apps/backend" && "$PY_ENV/bin/pip" install -e ".[dev]")
fi

echo "==> Ensuring sandbox Docker image mgx-sandbox:latest"
if command -v docker >/dev/null 2>&1; then
  if docker image inspect mgx-sandbox:latest >/dev/null 2>&1; then
    echo "    Docker image mgx-sandbox:latest already present, skipping build."
  else
    (cd "$ROOT_DIR/apps/backend/agents/docker/sandbox" && docker build -t mgx-sandbox:latest .)
  fi
else
  echo "docker command not found; skip sandbox image build. Install Docker and rerun setup if needed." >&2
fi

echo "Bootstrap complete."
