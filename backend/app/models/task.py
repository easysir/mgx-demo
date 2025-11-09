import uuid
from sqlalchemy import Column, String, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import Base

class Task(Base):
    """Task model for agent tasks."""
    __tablename__ = 'tasks'

    session_id = Column(UUID(as_uuid=True), ForeignKey('sessions.id'), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String, default="pending")  # pending, in_progress, completed, failed
    assignee = Column(String, nullable=True)  # Agent name
    result = Column(JSON, nullable=True)
    dependencies = Column(JSON, nullable=True)  # List of task IDs

    session = relationship("Session", back_populates="tasks")