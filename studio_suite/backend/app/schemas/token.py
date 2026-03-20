"""
Schemat tokena JWT
"""
from pydantic import BaseModel
from typing import Optional


class Token(BaseModel):
    """Schemat tokena dostępu"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Dane w tokenie"""
    username: Optional[str] = None
    role: Optional[str] = None
    tenant_id: Optional[int] = None
