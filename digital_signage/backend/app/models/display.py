"""
Model wyświetlacza
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class Display(Base):
    """Model wyświetlacza"""
    __tablename__ = "displays"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    mac_address = Column(String(17), unique=True, nullable=False, index=True)
    ip_address = Column(String(15), nullable=True)
    status = Column(
        String(20),
        default="offline",
        nullable=False,
        index=True
    )
    orientation = Column(Integer, default=0)
    resolution_width = Column(Integer, default=1920)
    resolution_height = Column(Integer, default=1080)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    floor = Column(String(50), nullable=True)
    position_x = Column(Integer, nullable=True)
    position_y = Column(Integer, nullable=True)
    last_seen = Column(DateTime(timezone=True), nullable=True)
    cache_size_mb = Column(Integer, default=1000)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    group = relationship("Group", back_populates="displays")

    __table_args__ = (
        CheckConstraint("status IN ('online', 'offline', 'error')", name="check_status"),
        CheckConstraint("orientation IN (0, 90, 180, 270)", name="check_orientation"),
    )

    def __repr__(self):
        return f"<Display(id={self.id}, name={self.name}, status={self.status})>"

