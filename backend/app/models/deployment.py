import uuid
from sqlalchemy import Column, String, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import Base

class Deployment(Base):
    """Deployment model."""
    __tablename__ = 'deployments'

    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False)
    platform = Column(String, nullable=False)  # 'vercel', 'netlify', etc.
    status = Column(String, default="pending")  # pending, deploying, success, failed
    url = Column(String, nullable=True)
    meta = Column(JSON, nullable=True)

    project = relationship("Project", back_populates="deployments")