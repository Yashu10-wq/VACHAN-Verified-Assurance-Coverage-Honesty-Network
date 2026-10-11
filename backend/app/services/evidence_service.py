"""
Secure Evidence Upload and Access Service for InsureChain VoiceGuard.
Enforces file format whitelisting, size restrictions, magic byte validation,
SHA-256 checksums, Cloudinary private asset uploads, signed URL generation,
and compensating transaction cleanups.
"""

from datetime import datetime, timezone
import hashlib
import io
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import uuid

import cloudinary
import cloudinary.uploader
import cloudinary.utils

from app.core.config import get_settings
from app.core.exceptions import IntegrationException, ValidationException
from app.core.logging import get_logger

logger = get_logger(__name__)

# Magic byte signatures for supported binary document types
MAGIC_BYTES = {
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/png": [b"\x89PNG\r\n\x1a\n"],
    "image/webp": [b"RIFF"],
    "application/pdf": [b"%PDF-"],
}

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".pdf"}


def compute_sha256(content: bytes) -> str:
    """Computes SHA-256 cryptographic checksum of file content."""
    return hashlib.sha256(content).hexdigest()


def validate_file(filename: str, content: bytes, declared_mime: str) -> str:
    """
    Validates file extension, declared MIME, size limits, and magic bytes.
    Returns normalized MIME type or raises ValidationException.
    """
    settings = get_settings()

    # 1. Check size limit
    if len(content) == 0:
        raise ValidationException("Uploaded file cannot be empty.")
    if len(content) > settings.MAX_EVIDENCE_FILE_SIZE_BYTES:
        raise ValidationException(
            f"File size ({len(content)} bytes) exceeds maximum permitted limit "
            f"of {settings.MAX_EVIDENCE_FILE_SIZE_BYTES} bytes ({settings.MAX_EVIDENCE_FILE_SIZE_BYTES // (1024 * 1024)}MB)."
        )

    # 2. Check extension
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationException(
            f"Invalid file extension '{ext}'. Allowed extensions are: {', '.join(sorted(ALLOWED_EXTENSIONS))}."
        )

    # 3. Check declared MIME
    norm_mime = declared_mime.lower().strip()
    if norm_mime not in settings.ALLOWED_EVIDENCE_MIME_TYPES:
        raise ValidationException(
            f"Unsupported MIME type '{declared_mime}'. Allowed MIME types: {', '.join(settings.ALLOWED_EVIDENCE_MIME_TYPES)}."
        )

    # 4. Verify magic bytes signature
    signatures = MAGIC_BYTES.get(norm_mime)
    if signatures:
        matched = False
        for sig in signatures:
            if norm_mime == "image/webp":
                if content.startswith(b"RIFF") and len(content) >= 12 and content[8:12] == b"WEBP":
                    matched = True
                    break
            elif content.startswith(sig):
                matched = True
                break
        if not matched:
            raise ValidationException(
                f"File content does not match declared MIME signature '{norm_mime}'."
            )

    return norm_mime


from urllib.parse import urlparse


class EvidenceStorageService:
    """Handles secure file upload and access via Cloudinary private storage."""

    def __init__(self) -> None:
        self._is_configured: bool = False
        self._cloud_name: Optional[str] = None
        self._api_key: Optional[str] = None
        self._api_secret: Optional[str] = None
        self._setup_cloudinary()

    def _setup_cloudinary(self) -> None:
        settings = get_settings()
        cloud_name = settings.CLOUDINARY_CLOUD_NAME
        api_key = settings.CLOUDINARY_API_KEY
        api_secret = settings.CLOUDINARY_API_SECRET

        if (not cloud_name or not api_key or not api_secret) and settings.CLOUDINARY_URL:
            try:
                parsed = urlparse(settings.CLOUDINARY_URL)
                if parsed.hostname:
                    cloud_name = cloud_name or parsed.hostname
                if parsed.username:
                    api_key = api_key or parsed.username
                if parsed.password:
                    api_secret = api_secret or parsed.password
            except Exception:
                pass

        if cloud_name and api_key and api_secret:
            if "<your_" not in api_key and "<your_" not in api_secret:
                self._cloud_name = cloud_name
                self._api_key = api_key
                self._api_secret = api_secret
                cloudinary.config(
                    cloud_name=cloud_name,
                    api_key=api_key,
                    api_secret=api_secret,
                    secure=True,
                )
                self._is_configured = True

    async def upload_evidence(
        self,
        claim_id: str,
        filename: str,
        content: bytes,
        declared_mime: str,
    ) -> Tuple[str, str, Dict[str, Any]]:
        """
        Validates and uploads evidence to Cloudinary private storage.
        Returns (document_storage_ref, checksum, resource_metadata).
        """
        norm_mime = validate_file(filename, content, declared_mime)
        checksum = compute_sha256(content)
        settings = get_settings()

        storage_id = f"claims/{claim_id}/evidence_{uuid.uuid4().hex[:12]}"
        resource_type = "raw" if norm_mime == "application/pdf" else "image"

        try:
            if self._is_configured:
                upload_result = cloudinary.uploader.upload(
                    file=io.BytesIO(content),
                    public_id=storage_id,
                    type="private",
                    resource_type=resource_type,
                    tags=["claim_evidence", f"claim_{claim_id}"],
                    overwrite=True,
                )
                metadata = {
                    "public_id": upload_result.get("public_id", storage_id),
                    "resource_type": resource_type,
                    "format": upload_result.get("format", norm_mime.split("/")[-1]),
                    "bytes": upload_result.get("bytes", len(content)),
                    "created_at": upload_result.get("created_at"),
                }
                return storage_id, checksum, metadata
            else:
                # Deterministic fallback storage identifier for unconfigured / mock runs
                metadata = {
                    "public_id": storage_id,
                    "resource_type": resource_type,
                    "format": norm_mime.split("/")[-1],
                    "bytes": len(content),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "mock": True,
                }
                return storage_id, checksum, metadata

        except Exception as exc:
            logger.error("Cloudinary upload failed: %s", type(exc).__name__)
            raise IntegrationException(
                service="Cloudinary",
                message="Failed to upload evidence document to secure storage.",
            ) from exc

    async def generate_signed_url(
        self,
        document_storage_ref: str,
        mime_type: str,
        expires_in_seconds: int = 300,
    ) -> str:
        """
        Generates a short-lived signed access URL for private evidence documents.
        """
        settings = get_settings()
        resource_type = "raw" if mime_type == "application/pdf" else "image"

        if self._is_configured:
            try:
                # Generate signed private delivery URL
                signed_url, _ = cloudinary.utils.cloudinary_url(
                    document_storage_ref,
                    type="private",
                    resource_type=resource_type,
                    sign_url=True,
                    secure=True,
                    expires_at=int(datetime.now(timezone.utc).timestamp()) + expires_in_seconds,
                )
                return signed_url
            except Exception as exc:
                logger.error("Failed to generate Cloudinary signed URL: %s", type(exc).__name__)
                raise IntegrationException(
                    service="Cloudinary",
                    message="Failed to generate secure signed access URL.",
                ) from exc
        else:
            # Deterministic mock signed URL for test environments
            return f"https://res.cloudinary.com/mock-cloud/{resource_type}/private/s--mock--/{document_storage_ref}?expires={expires_in_seconds}"

    async def delete_evidence_file(
        self,
        document_storage_ref: str,
        resource_type: str = "image",
    ) -> None:
        """
        Compensating cleanup: deletes uploaded file from Cloudinary if database persistence fails.
        """
        if not self._is_configured:
            return
        try:
            cloudinary.uploader.destroy(
                document_storage_ref,
                type="private",
                resource_type=resource_type,
            )
            logger.info("Successfully executed compensating cleanup for %s", document_storage_ref)
        except Exception as exc:
            logger.warning("Compensating cleanup for %s failed: %s", document_storage_ref, type(exc).__name__)


evidence_service = EvidenceStorageService()
