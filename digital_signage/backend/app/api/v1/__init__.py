"""
API v1 - rejestracja routerów
"""
from fastapi import APIRouter

from app.api.v1 import auth, displays, content, schedules, groups

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(displays.router)
api_router.include_router(content.router)
api_router.include_router(schedules.router)
api_router.include_router(groups.router)
