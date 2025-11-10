from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Dict, Optional

from app.services.stream import stream_manager


class SandboxFileWatcherManager:
  """Naive polling-based file watcher that broadcasts WebSocket events."""

  def __init__(self) -> None:
      self._tasks: Dict[str, asyncio.Task] = {}
      self._interval = float(os.getenv("SANDBOX_FILE_WATCH_INTERVAL", "2"))
      self._max_files = int(os.getenv("SANDBOX_FILE_WATCH_LIMIT", "4000"))

  def ensure_watch(self, session_id: str, root_path: Path) -> None:
      if session_id in self._tasks:
          return
      try:
          loop = asyncio.get_running_loop()
      except RuntimeError:
          return
      task = loop.create_task(self._watch_loop(session_id, root_path))
      self._tasks[session_id] = task

  def stop_watch(self, session_id: str) -> None:
      task = self._tasks.pop(session_id, None)
      if task:
          task.cancel()

  async def stop_all(self) -> None:
      for session_id in list(self._tasks.keys()):
          self.stop_watch(session_id)

  async def _watch_loop(self, session_id: str, root_path: Path) -> None:
      previous = self._snapshot(root_path)
      try:
          while True:
              await asyncio.sleep(self._interval)
              current = self._snapshot(root_path)
              changed = self._diff(previous, current)
              if changed:
                  await stream_manager.broadcast(
                      session_id,
                      {
                          "type": "file_change",
                          "paths": changed,
                      },
                  )
              previous = current
      except asyncio.CancelledError:
          pass

  def _snapshot(self, root_path: Path) -> Dict[str, float]:
      snapshot: Dict[str, float] = {}
      if not root_path.exists():
          return snapshot
      count = 0
      for directory, _, files in os.walk(root_path):
          for filename in files:
              if count >= self._max_files:
                  return snapshot
              path = Path(directory) / filename
              try:
                  snapshot[str(path)] = path.stat().st_mtime
              except FileNotFoundError:
                  continue
              count += 1
      return snapshot

  def _diff(self, previous: Dict[str, float], current: Dict[str, float]) -> list[str]:
      changed: set[str] = set()
      for path, mtime in current.items():
          if previous.get(path) != mtime:
              changed.add(path)
      for path in previous:
          if path not in current:
              changed.add(path)
      return list(changed)


file_watcher_manager = SandboxFileWatcherManager()
