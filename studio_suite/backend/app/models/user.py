"""
Model użytkownika
"""
from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.sql import func
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    """Role użytkowników"""
    ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"
    RECEPTIONIST = "receptionist"
    OPERATOR_DISPLAYS = "operator_displays"
    OPERATOR_BELLS = "operator_bells"
    OPERATOR = "operator"  # legacy alias; traktowany jak operator wyświetlaczy


class User(Base):
    """Model użytkownika"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.EMPLOYEE)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"
