from __future__ import annotations

from typing import Dict, Set, Any

from fastapi import WebSocket


class SessionStreamManager:
    """Manages WebSocket connections per session to broadcast streaming events."""

    def __init__(self) -> None:
        self._connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(session_id, set()).add(websocket)

    def disconnect(self, session_id: str, websocket: WebSocket) -> None:
        connections = self._connections.get(session_id)
        if not connections:
            return
        connections.discard(websocket)
        if not connections:
            self._connections.pop(session_id, None)

    async def broadcast(self, session_id: str, payload: Dict[str, Any]) -> None:
        payload.setdefault('session_id', session_id)
        connections = list(self._connections.get(session_id, []))
        for websocket in connections:
            try:
                await websocket.send_json(payload)
            except Exception:
                self.disconnect(session_id, websocket)


stream_manager = SessionStreamManager()
