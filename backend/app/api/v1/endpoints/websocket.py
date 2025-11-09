from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Dict
import json
from datetime import datetime

from app.services.session_manager import SessionManager
from app.dependencies import get_session_manager

router = APIRouter()

# 存储活跃的WebSocket连接
active_connections: Dict[str, WebSocket] = {}


class ConnectionManager:
    """管理WebSocket连接"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, session_id: str, websocket: WebSocket):
        """建立WebSocket连接"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        print(f"WebSocket连接已建立: session_id={session_id}")
    
    def disconnect(self, session_id: str):
        """断开WebSocket连接"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            print(f"WebSocket连接已断开: session_id={session_id}")
    
    async def send_message(self, session_id: str, message: dict):
        """向特定会话发送消息"""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            await websocket.send_json(message)
    
    async def broadcast(self, message: dict):
        """广播消息到所有连接"""
        for session_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"广播消息失败 session_id={session_id}: {e}")


# 全局连接管理器
manager = ConnectionManager()


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    token: str = Query(None),
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    WebSocket端点,用于实时双向通信
    
    客户端连接示例:
    ws://localhost:8000/api/v1/ws/{session_id}?token=your_jwt_token
    """
    
    # TODO: 在生产环境中,需要验证JWT token
    # if not token:
    #     await websocket.close(code=1008, reason="Missing authentication token")
    #     return
    
    # 验证会话是否存在
    session = await session_manager.get_session(session_id)
    if not session:
        await websocket.close(code=1008, reason="Session not found")
        return
    
    # 建立连接
    await manager.connect(session_id, websocket)
    
    try:
        # 发送欢迎消息
        await manager.send_message(session_id, {
            "type": "system_notification",
            "content": "WebSocket连接已建立",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # 持续监听客户端消息
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # 处理客户端消息
            if message_data.get("type") == "message":
                # 这里可以将消息路由到Mike Agent
                response = {
                    "type": "message",
                    "role": "assistant",
                    "content": f"收到消息: {message_data.get('content')}",
                    "timestamp": datetime.utcnow().isoformat()
                }
                await manager.send_message(session_id, response)
            
    except WebSocketDisconnect:
        manager.disconnect(session_id)
        print(f"客户端断开连接: session_id={session_id}")
    except Exception as e:
        print(f"WebSocket错误: {e}")
        manager.disconnect(session_id)


def get_connection_manager() -> ConnectionManager:
    """获取全局连接管理器实例"""
    return manager