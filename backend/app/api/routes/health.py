"""
Health and readiness endpoints for InsureChain VoiceGuard backend.
"""

from datetime import datetime, timezone
from typing import Any, Dict
from fastapi import APIRouter, Response, status

from app.core.config import get_settings
from app.core.exceptions import DatabaseException
from app.core.logging import get_logger
from app.db.connection import check_database_readiness
from app.integrations.cloudinary_client import CloudinaryClient
from app.integrations.elevenlabs_client import ElevenLabsClient
from app.integrations.gemini_client import GeminiClient

logger = get_logger(__name__)

router = APIRouter(tags=["Health & Diagnostics"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_liveness() -> Dict[str, Any]:
    """
    Application liveness probe.
    Confirms API process is alive and responding.
    Does NOT require database or third-party connectivity.
    """
    settings = get_settings()
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/ready")
async def health_readiness(response: Response) -> Dict[str, Any]:
    """
    Application readiness probe.
    Verifies actual connectivity to Neon Cloud PostgreSQL via Psycopg 3.
    Returns HTTP 200 on success; HTTP 503 on database unavailability.
    Never exposes credentials, connection strings, or internal traces.
    """
    settings = get_settings()
    timestamp = datetime.now(timezone.utc).isoformat()

    try:
        is_ready = await check_database_readiness(timeout_seconds=float(settings.DATABASE_CONNECT_TIMEOUT))
        if is_ready:
            return {
                "status": "ready",
                "database": "connected",
                "host": settings.get_sanitized_database_host(),
                "timestamp": timestamp,
            }
        else:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            return {
                "status": "unready",
                "database": "unavailable",
                "message": "Database readiness check did not return expected response.",
                "timestamp": timestamp,
            }
    except DatabaseException as exc:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "unready",
            "database": "disconnected",
            "message": exc.message,
            "timestamp": timestamp,
        }
    except Exception as exc:
        logger.error("Unexpected error during readiness check: %s", type(exc).__name__)
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "unready",
            "database": "error",
            "message": "Database service is temporarily unavailable.",
            "timestamp": timestamp,
        }


@router.get("/health/integrations", status_code=status.HTTP_200_OK)
async def health_integrations() -> Dict[str, Any]:
    """
    Non-sensitive diagnostic overview of configured integrations.
    Does NOT call paid external APIs.
    """
    cloudinary = CloudinaryClient()
    elevenlabs = ElevenLabsClient()
    gemini = GeminiClient()

    return {
        "integrations": {
            "cloudinary": cloudinary.get_status(),
            "elevenlabs": elevenlabs.get_status(),
            "gemini": gemini.get_status(),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
