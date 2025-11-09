#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APP_DIR="${ROOT_DIR}/apps/backend"
PY_ENV="${HOME}/venvs/mgx"

if [ ! -d "$PY_ENV" ]; then
  echo "Python 虚拟环境未找到：${PY_ENV}，请先运行 pnpm run setup。" >&2
  exit 1
fi

echo "==> Starting FastAPI backend using ${PY_ENV}"
cd "$APP_DIR"
"${PY_ENV}/bin/python" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

