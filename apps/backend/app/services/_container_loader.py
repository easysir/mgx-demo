"""Utility to ensure the container_app package is importable within the monorepo."""

from __future__ import annotations

import sys
from pathlib import Path

_CONTAINER_APP_PATH = Path(__file__).resolve().parents[3] / "container"
if _CONTAINER_APP_PATH.exists():
    _path_str = str(_CONTAINER_APP_PATH)
    if _path_str not in sys.path:
        sys.path.append(_path_str)

__all__ = ["_CONTAINER_APP_PATH"]
