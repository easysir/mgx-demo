import uuid
from sqlalchemy import Column, String, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import Base

class Session(Base):
    """Session model representing a single chat or development session."""
    __tablename__ = 'sessions'

    name = Column(String, default="New Session")
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False)
    context = Column(JSON, nullable=True)  # Short-term context

    user = relationship("User", back_populates="sessions")
    project = relationship("Project", back_populates="sessions")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="session", cascade="all, delete-orphan")