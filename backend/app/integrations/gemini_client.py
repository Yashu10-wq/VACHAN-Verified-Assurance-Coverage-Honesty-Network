"""
Google Gemini AI integration configuration module for InsureChain VoiceGuard.
Prepares for promise extraction vs actual policy clause comparison.
Does not make paid AI calls or mock responses in Phase 1.
"""

from enum import Enum
from typing import Dict, List, Optional

from app.core.config import get_settings
from app.core.exceptions import IntegrationException
from app.core.logging import get_logger

logger = get_logger(__name__)


class PromiseVerdict(str, Enum):
    """Grounded comparison classifications for agent commitments vs policy clauses."""

    SUPPORTED = "SUPPORTED"
    PARTLY_TRUE = "PARTLY_TRUE"
    CONTRADICTED = "CONTRADICTED"
    NOT_IN_POLICY = "NOT_IN_POLICY"
    UNCLEAR = "UNCLEAR"


class GeminiClient:
    """Configuration and initialization interface for Google Gemini comparator."""

    def __init__(self) -> None:
        self._api_key: Optional[str] = None
        self._is_configured: bool = False
        self._resolve_configuration()

    def _resolve_configuration(self) -> None:
        settings = get_settings()
        key = settings.GEMINI_API_KEY
        if key and key.strip() and "your_" not in key:
            self._api_key = key.strip()
            self._is_configured = True

    def validate_configuration(self) -> bool:
        """
        Validates that GEMINI_API_KEY is configured.
        Raises IntegrationException if invoked when unconfigured.
        """
        if not self._is_configured:
            raise IntegrationException(
                service="Google Gemini",
                message="GEMINI_API_KEY is not configured.",
            )
        return True

    def get_status(self) -> Dict[str, object]:
        """Returns non-sensitive status report."""
        return {
            "service": "Google Gemini",
            "configured": self._is_configured,
            "supported_verdicts": [v.value for v in PromiseVerdict],
            "ready_for_phase2": self._is_configured,
        }
