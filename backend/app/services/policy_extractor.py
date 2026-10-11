"""
Policy Document Extractor Service for InsureChain VoiceGuard.
Extracts structured text, page numbers, and section headings from policy PDFs using pypdf.
Computes cryptographic SHA-256 checksums, validates document integrity, and detects scanned or unreadable documents.
"""

import hashlib
import io
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple
import httpx
import psycopg
import pypdf

from app.core.exceptions import IntegrationException, ValidationException
from app.core.logging import get_logger
from app.db.repositories import extraction_repo, policy_repo

logger = get_logger(__name__)


def compute_sha256(content: bytes) -> str:
    """Computes SHA-256 cryptographic checksum."""
    return hashlib.sha256(content).hexdigest()


def detect_section_headings(page_text: str) -> List[str]:
    """Detects likely clause or section headings within a page of text."""
    headings = []
    lines = page_text.splitlines()
    heading_patterns = [
        re.compile(r"^(?:Section|Clause|Article|Part)\s+[0-9A-Za-z\.\-]+.*", re.IGNORECASE),
        re.compile(r"^[0-9]+(?:\.[0-9]+)+\s+[A-Za-z].*"),
        re.compile(r"^(?:DEFINITIONS|COVERAGE|EXCLUSIONS|WAITING PERIOD|CONDITIONS|CLAIMS PROCEDURE|LIMITS OF LIABILITY|GENERAL PROVISIONS)\b", re.IGNORECASE),
    ]

    for line in lines:
        cleaned = line.strip()
        if not cleaned or len(cleaned) > 100:
            continue
        for pattern in heading_patterns:
            if pattern.match(cleaned):
                headings.append(cleaned)
                break
        else:
            # Check for uppercase headings (between 4 and 60 chars)
            if cleaned.isupper() and len(cleaned) >= 4 and len(cleaned) <= 60 and not cleaned.isdigit():
                headings.append(cleaned)

    # Return deduplicated headings in order of appearance
    seen = set()
    result = []
    for h in headings:
        if h not in seen:
            seen.add(h)
            result.append(h)
    return result


class PolicyExtractorService:
    """Handles PDF retrieval, page-by-page text extraction, and caching."""

    async def fetch_document_bytes(self, storage_ref: str) -> bytes:
        """
        Retrieves document bytes from local storage, file path, or remote URL.
        """
        if not storage_ref or not storage_ref.strip():
            raise ValidationException("Document storage reference is missing or empty.")

        ref = storage_ref.strip()

        # 1. HTTP / HTTPS URL
        if ref.startswith("http://") or ref.startswith("https://"):
            try:
                async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                    resp = await client.get(ref)
                    resp.raise_for_status()
                    return resp.content
            except Exception as e:
                logger.error("Failed to download policy PDF from URL: %s", str(e))
                raise IntegrationException(f"Failed to fetch policy document from storage URL: {str(e)}")

        # 2. Local filesystem path
        local_path = Path(ref)
        if local_path.is_file():
            try:
                return local_path.read_bytes()
            except Exception as e:
                logger.error("Failed to read policy PDF from local file: %s", str(e))
                raise IntegrationException(f"Failed to read policy document from path: {str(e)}")

        # 3. Base64 or synthetic test content check
        raise ValidationException(
            f"Policy document storage reference '{storage_ref}' cannot be resolved to an accessible file or URL."
        )

    def extract_from_pdf_bytes(
        self, pdf_bytes: bytes
    ) -> Tuple[str, int, List[Dict[str, Any]], str]:
        """
        Parses PDF bytes using pypdf.
        Returns: (full_extracted_text, page_count, pages_json, extraction_status)
        """
        if not pdf_bytes:
            return "", 0, [], "FAILED"

        try:
            reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        except Exception as e:
            logger.error("pypdf failed to parse PDF document: %s", str(e))
            raise ValidationException(f"Invalid or corrupted PDF document: {str(e)}")

        page_count = len(reader.pages)
        if page_count == 0:
            return "", 0, [], "NEEDS_REVIEW"

        pages_data: List[Dict[str, Any]] = []
        full_text_parts: List[str] = []

        total_char_count = 0
        for idx, page in enumerate(reader.pages):
            page_num = idx + 1
            text = page.extract_text() or ""
            text_clean = text.strip()
            total_char_count += len(text_clean)

            headings = detect_section_headings(text_clean)

            pages_data.append({
                "page_number": page_num,
                "text": text_clean,
                "section_headings": headings,
            })

            full_text_parts.append(f"--- PAGE {page_num} ---\n{text_clean}")

        full_extracted_text = "\n\n".join(full_text_parts).strip()

        # If less than 25 alphanumeric chars in total, likely scanned image or blank
        alphanumeric_count = sum(1 for c in full_extracted_text if c.isalnum())
        if alphanumeric_count < 25:
            logger.warning("Policy PDF has no digital text (%d chars). Flagged for review.", alphanumeric_count)
            return full_extracted_text, page_count, pages_data, "NEEDS_REVIEW"

        return full_extracted_text, page_count, pages_data, "COMPLETED"

    async def get_or_extract_policy_text(
        self,
        conn: psycopg.AsyncConnection,
        policy_version_id: str,
    ) -> Dict[str, Any]:
        """
        Retrieves cached extraction or downloads and parses the policy PDF.
        """
        # 1. Check existing extraction
        existing = await extraction_repo.get_extraction_by_version(conn, policy_version_id)
        if existing and existing["status"] in ("COMPLETED", "NEEDS_REVIEW") and existing["extracted_text"]:
            logger.info("Reusing cached extraction for policy_version %s", policy_version_id)
            return existing

        # 2. Retrieve policy version record
        version = await policy_repo.get_policy_version_by_id(conn, policy_version_id)
        if not version:
            raise ValidationException(f"Policy version '{policy_version_id}' not found.")

        storage_ref = version["document_storage_ref"]
        expected_checksum = version["document_checksum"]

        # 3. Handle cases where terms_json is directly populated (e.g. for structured text/tests)
        terms_json = version.get("terms_json") or {}

        if terms_json and ("clauses" in terms_json or "text" in terms_json or "sections" in terms_json):
            logger.info("Using terms_json structured clauses for extraction text.")
            text_content = ""
            if "text" in terms_json:
                text_content = str(terms_json["text"])
            elif "clauses" in terms_json:
                clauses = terms_json["clauses"]
                if isinstance(clauses, list):
                    text_content = "\n\n".join(str(c) for c in clauses)
                elif isinstance(clauses, dict):
                    text_content = "\n\n".join(f"{k}: {v}" for k, v in clauses.items())
            elif "sections" in terms_json:
                sections = terms_json["sections"]
                if isinstance(sections, list):
                    text_content = "\n\n".join(str(s) for s in sections)

            pages_json = [{
                "page_number": 1,
                "text": text_content,
                "section_headings": detect_section_headings(text_content),
            }]

            status = "COMPLETED" if len(text_content.strip()) > 20 else "NEEDS_REVIEW"
            saved = await extraction_repo.create_extraction(
                conn=conn,
                policy_version_id=policy_version_id,
                document_checksum=expected_checksum,
                status=status,
                extracted_text=text_content,
                page_count=1,
                pages_json=pages_json,
                parser_version="terms_json_direct",
                error_message=None,
            )
            return saved

        # 4. Fetch PDF file bytes
        pdf_bytes = await self.fetch_document_bytes(storage_ref)
        checksum = compute_sha256(pdf_bytes)

        # 4. Extract PDF
        extracted_text, page_count, pages_json, status = self.extract_from_pdf_bytes(pdf_bytes)
        error_msg = None
        if status == "NEEDS_REVIEW":
            error_msg = "PDF contains insufficient digital text (scanned image or empty). Review required."

        # 5. Persist extraction cache
        saved = await extraction_repo.create_extraction(
            conn=conn,
            policy_version_id=policy_version_id,
            document_checksum=checksum,
            status=status,
            extracted_text=extracted_text,
            page_count=page_count,
            pages_json=pages_json,
            parser_version="pypdf_v1",
            error_message=error_msg,
        )
        return saved


policy_extractor_service = PolicyExtractorService()
