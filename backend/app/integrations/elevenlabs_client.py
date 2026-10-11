"""
ElevenLabs Voice AI integration configuration module for InsureChain VoiceGuard.
Prepares for Speech-to-Text transcription and TTS spoken claim decision explanations.
Does not make paid API requests or mock external AI responses in Phase 1.
"""

from typing import Dict, Optional

from app.core.config import get_settings
from app.core.exceptions import IntegrationException
from app.core.logging import get_logger

logger = get_logger(__name__)


class ElevenLabsClient:
    """Configuration and initialization interface for ElevenLabs Voice AI."""

    def __init__(self) -> None:
        self._api_key: Optional[str] = None
        self._is_configured: bool = False
        self._resolve_configuration()

    def _resolve_configuration(self) -> None:
        settings = get_settings()
        key = settings.ELEVENLABS_API_KEY
        if key and key.strip() and "your_" not in key:
            self._api_key = key.strip()
            self._is_configured = True

    def validate_configuration(self) -> bool:
        """
        Validates that ELEVENLABS_API_KEY is configured.
        Raises IntegrationException if invoked when unconfigured.
        """
        if not self._is_configured:
            raise IntegrationException(
                service="ElevenLabs",
                message="ELEVENLABS_API_KEY is not configured.",
            )
        return True

    def get_status(self) -> Dict[str, object]:
        """Returns non-sensitive status report."""
        return {
            "service": "ElevenLabs",
            "configured": self._is_configured,
            "capabilities": [
                "Speech-to-Text (sales recording transcription)",
                "Text-to-Speech (spoken decision explanations)",
            ],
            "ready_for_phase2": self._is_configured,
        }
