"""
Structured logging module with automatic secret redaction.
Ensures passwords, tokens, API keys, and connection strings are masked.
"""

import logging
import re
import sys
from typing import Any

# Regex patterns matching sensitive values to redact
SENSITIVE_PATTERNS = [
    # Database connection strings with credentials: postgresql://user:pass@host
    (re.compile(r"(postgres(?:ql)?:\/\/[^:]+:)([^@]+)(@)", re.IGNORECASE), r"\1***\3"),
    # Generic API keys, secrets, or tokens in key=val or json patterns
    (
        re.compile(
            r"(api[_-]?key|secret|password|token|bearer|gemini_api_key|cloudinary_api_secret|elevenlabs_api_key)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.]{8,})['\"]?",
            re.IGNORECASE,
        ),
        r"\1=***",
    ),
]


class RedactingFormatter(logging.Formatter):
    """Custom formatter that scrubs credentials and sensitive tokens from log records."""

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        for pattern, replacement in SENSITIVE_PATTERNS:
            message = pattern.sub(replacement, message)
        return message


def setup_logging(log_level: str = "INFO") -> None:
    """Configures structured console logging with secret scrubbing."""
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    formatter = RedactingFormatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Avoid duplicate handlers if setup_logging is called multiple times
    root_logger.handlers = [handler]

    # Suppress overly chatty third-party loggers if needed
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Retrieves a named logger instance."""
    return logging.getLogger(name)
