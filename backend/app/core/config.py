"""
Centralized settings management for InsureChain VoiceGuard backend.
Uses Pydantic Settings to load and validate environment variables safely.
"""

from functools import lru_cache
import re
from typing import List, Optional
from urllib.parse import urlparse

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.exceptions import ConfigurationException


class Settings(BaseSettings):
    """Application runtime configuration."""

    # Application settings
    APP_NAME: str = Field(default="InsureChain VoiceGuard Backend")
    APP_ENV: str = Field(default="development")
    API_V1_PREFIX: str = Field(default="/api/v1")
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    LOG_LEVEL: str = Field(default="INFO")

    # CORS allowlist for frontend origins
    FRONTEND_ORIGINS: List[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://localhost:3000"]
    )

    # Database configuration (Neon Cloud PostgreSQL strictly required)
    DATABASE_URL: Optional[str] = Field(default=None)
    DB_URI: Optional[str] = Field(default=None)  # Alternative env key support
    DATABASE_CONNECT_TIMEOUT: int = Field(default=10)

    # Cloudinary configuration (private storage for sales recordings & documents)
    CLOUDINARY_CLOUD_NAME: Optional[str] = Field(default=None)
    CLOUDINARY_API_KEY: Optional[str] = Field(default=None)
    CLOUDINARY_API_SECRET: Optional[str] = Field(default=None)
    CLOUDINARY_URL: Optional[str] = Field(default=None)
    MAX_EVIDENCE_FILE_SIZE_BYTES: int = Field(default=10 * 1024 * 1024)  # 10 MB
    ALLOWED_EVIDENCE_MIME_TYPES: List[str] = Field(
        default_factory=lambda: [
            "image/jpeg",
            "image/png",
            "image/webp",
            "application/pdf",
        ]
    )

    # ElevenLabs Voice AI (Speech-to-Text transcription & TTS explanations)
    ELEVENLABS_API_KEY: Optional[str] = Field(default=None)
    ELEVEN_LABS_API_KEY: Optional[str] = Field(default=None)
    ELEVENLABS_STT_MODEL: str = Field(default="scribe_v2")
    MAX_AUDIO_FILE_SIZE_BYTES: int = Field(default=50 * 1024 * 1024)  # 50 MB
    ALLOWED_AUDIO_MIME_TYPES: List[str] = Field(
        default_factory=lambda: [
            "audio/mpeg",
            "audio/mp3",
            "audio/wav",
            "audio/m4a",
            "audio/x-m4a",
            "audio/ogg",
            "audio/webm",
        ]
    )
    RUN_LIVE_ELEVENLABS_TEST: bool = Field(default=False)

    # Google Gemini AI (Promise extraction vs policy clause comparison)
    GEMINI_API_KEY: Optional[str] = Field(default=None)

    # Security & JWT Authentication
    JWT_SECRET_KEY: str = Field(default="insurechain_jwt_secret_production_key_32bytes_vachan")
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)
    EMAIL_VERIFICATION_EXPIRE_HOURS: int = Field(default=24)
    PASSWORD_RESET_EXPIRE_HOURS: int = Field(default=1)
    CUSTOMER_ACTIVATION_EXPIRE_HOURS: int = Field(default=48)

    # Operator Authority Bootstrap Secret
    AUTHORITY_BOOTSTRAP_SECRET: Optional[str] = Field(default="vortexa3_operator_bootstrap_secret_secure")

    # Email Service
    EMAIL_PROVIDER: str = Field(default="console")  # console, smtp, test
    EMAIL_FROM: str = Field(default="noreply@insurechain-voiceguard.local")
    SMTP_HOST: Optional[str] = Field(default=None)
    SMTP_PORT: int = Field(default=587)
    SMTP_USERNAME: Optional[str] = Field(default=None)
    SMTP_PASSWORD: Optional[str] = Field(default=None)
    APP_URL: str = Field(default="http://localhost:5173")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("FRONTEND_ORIGINS", mode="before")
    @classmethod
    def parse_frontend_origins(cls, value: object) -> List[str]:
        """Supports comma-separated strings or list of strings for FRONTEND_ORIGINS."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        if isinstance(value, list):
            return [str(origin).strip() for origin in value if str(origin).strip()]
        return ["http://localhost:5173", "http://localhost:3000"]

    def get_database_url(self) -> str:
        """
        Retrieves and validates the active Neon PostgreSQL connection string.
        Raises ConfigurationException if absent or not a PostgreSQL URL.
        """
        raw_url = self.DATABASE_URL or self.DB_URI
        if not raw_url or not raw_url.strip():
            raise ConfigurationException(
                "Database connection string is missing. "
                "Please configure DATABASE_URL or DB_URI in your environment."
            )

        clean_url = raw_url.strip()
        if not (clean_url.startswith("postgresql://") or clean_url.startswith("postgres://")):
            raise ConfigurationException(
                "Invalid database scheme. InsureChain VoiceGuard strictly requires "
                "a Neon PostgreSQL connection string starting with 'postgresql://'."
            )

        return clean_url

    def get_sanitized_database_host(self) -> str:
        """Returns the database host without exposing credentials."""
        try:
            url = self.get_database_url()
            parsed = urlparse(url)
            return parsed.hostname or "unknown-host"
        except Exception:
            return "unconfigured"


@lru_cache()
def get_settings() -> Settings:
    """Returns cached application settings singleton."""
    return Settings()
