import uuid
from sqlalchemy import Column, String, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import Base

class Message(Base):
    """Message model for chat history."""
    __tablename__ = 'messages'

    session_id = Column(UUID(as_uuid=True), ForeignKey('sessions.id'), nullable=False)
    sender = Column(String, nullable=False)  # 'user' or agent name
    content = Column(Text, nullable=False)
    message_type = Column(String, default="text")  # 'text', 'code', 'tool_call', 'tool_result'
    meta = Column(JSON, nullable=True)

    session = relationship("Session", back_populates="messages")