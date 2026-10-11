"""
Cloudinary integration configuration module for InsureChain VoiceGuard.
Prepares for private storage of sales recordings and policy documents.
Does not perform actual uploads or expose API secrets.
"""

from typing import Dict, Optional
from urllib.parse import urlparse

from app.core.config import get_settings
from app.core.exceptions import IntegrationException
from app.core.logging import get_logger

logger = get_logger(__name__)


class CloudinaryClient:
    """Configuration and initialization interface for Cloudinary private storage."""

    def __init__(self) -> None:
        self._cloud_name: Optional[str] = None
        self._api_key: Optional[str] = None
        self._is_configured: bool = False
        self._resolve_configuration()

    def _resolve_configuration(self) -> None:
        """Resolves configuration from explicit env variables or CLOUDINARY_URL."""
        settings = get_settings()

        cloud_name = settings.CLOUDINARY_CLOUD_NAME
        api_key = settings.CLOUDINARY_API_KEY
        api_secret = settings.CLOUDINARY_API_SECRET

        # If CLOUDINARY_URL is provided (e.g. cloudinary://api_key:api_secret@cloud_name)
        if (not cloud_name or not api_key or not api_secret) and settings.CLOUDINARY_URL:
            try:
                parsed = urlparse(settings.CLOUDINARY_URL)
                if parsed.hostname:
                    cloud_name = cloud_name or parsed.hostname
                if parsed.username:
                    api_key = api_key or parsed.username
                if parsed.password:
                    api_secret = api_secret or parsed.password
            except Exception as exc:
                logger.warning("Could not parse CLOUDINARY_URL: %s", type(exc).__name__)

        if cloud_name and api_key and api_secret:
            # Exclude placeholder values
            if "<your_" not in api_key and "<your_" not in api_secret:
                self._cloud_name = cloud_name
                self._api_key = api_key
                self._is_configured = True

    def validate_configuration(self) -> bool:
        """
        Validates that required Cloudinary parameters are configured.
        Raises IntegrationException if invoked when unconfigured.
        """
        if not self._is_configured:
            raise IntegrationException(
                service="Cloudinary",
                message="Missing required credentials (cloud_name, api_key, api_secret).",
            )
        return True

    def get_status(self) -> Dict[str, object]:
        """Returns non-sensitive status report."""
        return {
            "service": "Cloudinary",
            "configured": self._is_configured,
            "cloud_name": self._cloud_name if self._is_configured else None,
            "ready_for_phase2": self._is_configured,
        }
