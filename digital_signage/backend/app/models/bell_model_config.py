from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.types import JSON

from app.database import Base


class BellModelConfig(Base):
    __tablename__ = "bell_model_configs"

    id = Column(Integer, primary_key=True, index=True)
    model_json = Column(JSON, nullable=False)
    revision = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
