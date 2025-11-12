from __future__ import annotations

import asyncio
import logging
from typing import Optional

from .container import container_manager

logger = logging.getLogger(__name__)


class SandboxIdleReaper:
    def __init__(self, interval_seconds: int) -> None:
        self._interval = max(5, interval_seconds)
        self._task: Optional[asyncio.Task[None]] = None
        self._stop_event: Optional[asyncio.Event] = None

    async def start(self) -> None:
        if self._task:
            return
        self._stop_event = asyncio.Event()
        self._task = asyncio.create_task(self._run(), name="sandbox-idle-reaper")
        logger.info("SandboxIdleReaper started (interval=%ss)", self._interval)

    async def stop(self) -> None:
        if not self._task or not self._stop_event:
            return
        self._stop_event.set()
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        finally:
            self._task = None
            self._stop_event = None
        logger.info("SandboxIdleReaper stopped")

    async def _run(self) -> None:
        assert self._stop_event is not None
        while not self._stop_event.is_set():
            try:
                released = container_manager.cleanup_idle()
                if released:
                    logger.info(
                        "SandboxIdleReaper cleaned %d idle sandboxes: %s",
                        len(released),
                        ", ".join(released),
                    )
            except Exception:
                logger.exception("SandboxIdleReaper: cleanup failed")

            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self._interval)
            except asyncio.TimeoutError:
                continue


sandbox_idle_reaper = SandboxIdleReaper(
    interval_seconds=container_manager.config.gc_interval_seconds or 300
)

__all__ = ["sandbox_idle_reaper", "SandboxIdleReaper"]
