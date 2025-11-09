import uuid
from sqlalchemy import Column, String, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import Base

class Project(Base):
    """Project model."""
    __tablename__ = 'projects'

    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    meta = Column(JSON, nullable=True)

    owner = relationship("User", back_populates="projects")
    sessions = relationship("Session", back_populates="project")
    files = relationship("File", back_populates="project")
    deployments = relationship("Deployment", back_populates="project")