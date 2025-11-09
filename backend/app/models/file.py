import uuid
from sqlalchemy import Column, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import Base

class File(Base):
    """File model for project files."""
    __tablename__ = 'files'

    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False)
    path = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    
    project = relationship("Project", back_populates="files")