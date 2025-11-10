from __future__ import annotations

from collections import deque
from typing import Any, Deque, Dict, Optional, Set

from fastapi import WebSocket


class SessionStreamManager:
    """Manages WebSocket connections per session to broadcast streaming events."""

    def __init__(self) -> None:
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._buffers: Dict[str, Deque[Dict[str, Any]]] = {}
        self._sequence: Dict[str, int] = {}

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(session_id, set()).add(websocket)
        buffer = self._buffers.get(session_id)
        if buffer:
            for event in buffer:
                await self._safe_send(websocket, event)

    def disconnect(self, session_id: str, websocket: WebSocket) -> None:
        connections = self._connections.get(session_id)
        if not connections:
            return
        connections.discard(websocket)
        if not connections:
            self._connections.pop(session_id, None)

    async def broadcast(self, session_id: str, payload: Dict[str, Any]) -> None:
        event = {'session_id': session_id, **payload}
        event['sequence'] = self._next_sequence(session_id)
        buffer = self._buffers.setdefault(session_id, deque(maxlen=200))
        buffer.append(event)
        connections = list(self._connections.get(session_id, []))
        for websocket in connections:
            await self._safe_send(websocket, event)

    async def _safe_send(self, websocket: WebSocket, payload: Dict[str, Any]) -> None:
        try:
            await websocket.send_json(payload)
        except Exception:
            # best-effort cleanup; caller负责继续广播
            for session_id, sockets in list(self._connections.items()):
                if websocket in sockets:
                    self.disconnect(session_id, websocket)
                    break

    def _next_sequence(self, session_id: str) -> int:
        current = self._sequence.get(session_id, 0) + 1
        self._sequence[session_id] = current
        return current


stream_manager = SessionStreamManager()
