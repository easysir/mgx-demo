from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

AgentRole = Literal['Mike', 'Emma', 'Bob', 'Alex', 'David', 'Iris']
SenderRole = Literal['user', 'mike', 'agent', 'status']


class Message(BaseModel):
    id: str
    session_id: str
    sender: SenderRole
    content: str
    timestamp: datetime
    agent: Optional[AgentRole] = None


class Session(BaseModel):
    id: str
    title: str
    created_at: datetime
    owner_id: str
    messages: list[Message] = Field(default_factory=list)


class SessionCreate(BaseModel):
    title: Optional[str] = None


class SessionResponse(Session):
    pass


class MessageCreate(BaseModel):
    session_id: str
    content: str = Field(min_length=1, max_length=4000)


class ChatTurn(BaseModel):
    user: Message
    responses: list[Message]
