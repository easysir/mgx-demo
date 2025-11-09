from sqlalchemy import Column, String, JSON, Boolean
from sqlalchemy.orm import relationship
from .base import Base

class User(Base):
    """User model."""
    __tablename__ = 'users'

    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    meta = Column(JSON, nullable=True)

    projects = relationship("Project", back_populates="owner")
    sessions = relationship("Session", back_populates="user")