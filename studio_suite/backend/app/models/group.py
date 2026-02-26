"""
Model grupy wyświetlaczy
"""
from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class Group(Base):
    """Model grupy wyświetlaczy"""
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    type = Column(String(20), nullable=False)
    floor = Column(String(50), nullable=True)
    layout_config = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    displays = relationship("Display", back_populates="group")

    def __repr__(self):
        return f"<Group(id={self.id}, name={self.name}, type={self.type})>"

