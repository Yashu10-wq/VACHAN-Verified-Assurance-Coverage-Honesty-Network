"""
Cryptographic security, password hashing, and token helpers for InsureChain VoiceGuard.
Uses Argon2id for password hashing and PyJWT with HS256 for signed access tokens.
"""

from datetime import datetime, timedelta, timezone
from enum import Enum
import hashlib
import secrets
from typing import Any, Dict, Optional

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import jwt

from app.core.config import get_settings
from app.core.exceptions import AuthenticationException
from app.core.logging import get_logger

logger = get_logger(__name__)

# Argon2id password hasher with secure defaults
_hasher = PasswordHasher()


class UserRole(str, Enum):
    """Supported system user roles."""

    CUSTOMER = "CUSTOMER"
    INSURANCE_AGENT = "INSURANCE_AGENT"
    APPROVAL_AUTHORITY = "APPROVAL_AUTHORITY"


class AccountStatus(str, Enum):
    """Account authorization lifecycle states."""

    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    ACTIVE = "ACTIVE"
    REJECTED = "REJECTED"
    SUSPENDED = "SUSPENDED"


class TokenType(str, Enum):
    """Single-use token classifications."""

    EMAIL_VERIFICATION = "EMAIL_VERIFICATION"
    PASSWORD_RESET = "PASSWORD_RESET"
    CUSTOMER_ACTIVATION = "CUSTOMER_ACTIVATION"


class RegistrationStatus(str, Enum):
    """Policy registration lifecycle states."""

    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    PENDING_REVIEW = "PENDING_REVIEW"
    AWAITING_CUSTOMER_CONFIRMATION = "AWAITING_CUSTOMER_CONFIRMATION"
    CONFIRMED = "CONFIRMED"
    DECLINED = "DECLINED"
    CANCELLED = "CANCELLED"


class PolicyCategory(str, Enum):
    """Insurance scheme categories."""

    VEHICLE = "VEHICLE"
    HOSPITALIZATION = "HOSPITALIZATION"
    MEDICAL = "MEDICAL"
    GENERIC = "GENERIC"


class ClaimCategory(str, Enum):
    """Supported claim categories."""

    VEHICLE = "VEHICLE"
    MEDICAL = "MEDICAL"
    GENERIC = "GENERIC"


class ClaimStatus(str, Enum):
    """Strict claim lifecycle states."""

    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    EVIDENCE_REQUESTED = "EVIDENCE_REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PAID = "PAID"


class EvidenceType(str, Enum):
    """Categories of supporting claim evidence documents."""

    REGISTRATION_CERTIFICATE = "REGISTRATION_CERTIFICATE"
    DRIVING_LICENSE = "DRIVING_LICENSE"
    INCIDENT_PHOTO = "INCIDENT_PHOTO"
    REPAIR_ESTIMATE = "REPAIR_ESTIMATE"
    MEDICAL_BILL = "MEDICAL_BILL"
    DISCHARGE_SUMMARY = "DISCHARGE_SUMMARY"
    PRESCRIPTION = "PRESCRIPTION"
    MEDICAL_REPORT = "MEDICAL_REPORT"
    SUPPORTING_DOCUMENT = "SUPPORTING_DOCUMENT"


class AssessmentOutcome(str, Enum):
    """Overall outcome of deterministic eligibility evaluation."""

    ELIGIBLE = "ELIGIBLE"
    INELIGIBLE = "INELIGIBLE"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class RuleOutcome(str, Enum):
    """Individual rule evaluation outcome."""

    PASS = "PASS"
    FAIL = "FAIL"
    NEEDS_REVIEW = "NEEDS_REVIEW"


def hash_password(password: str) -> str:
    """Hashes a password using Argon2id."""
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verifies a plain password against an Argon2id hash."""
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, Exception):
        return False


def generate_secure_token() -> str:
    """Generates a high-entropy URL-safe one-time token."""
    return secrets.token_urlsafe(32)


def hash_token(raw_token: str) -> str:
    """Computes a deterministic SHA-256 hash of a raw token for storage."""
    return hashlib.sha256(raw_token.strip().encode("utf-8")).hexdigest()


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Creates a signed JWT access token."""
    settings = get_settings()
    to_encode = data.copy()

    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"iat": now, "exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decodes and validates a signed JWT access token.
    Raises AuthenticationException on expiration or signature invalidity.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except jwt.ExpiredSignatureError as exc:
        raise AuthenticationException("Access token has expired.") from exc
    except jwt.PyJWTError as exc:
        raise AuthenticationException("Invalid access token.") from exc
