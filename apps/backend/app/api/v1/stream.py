from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.stream import stream_manager

router = APIRouter()


@router.websocket("/ws/sessions/{session_id}")
async def session_stream(websocket: WebSocket, session_id: str) -> None:
    await stream_manager.connect(session_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        stream_manager.disconnect(session_id, websocket)
