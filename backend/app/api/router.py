"""
Central API router registering all sub-routers under /api/v1.
"""

from fastapi import APIRouter
from app.api.routes import auth, claims, health, policies, registrations

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(policies.router)
api_router.include_router(registrations.router)
api_router.include_router(claims.router)
