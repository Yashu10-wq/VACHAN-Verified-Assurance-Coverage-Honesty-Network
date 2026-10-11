"""
Pydantic validation schemas for sales recording sessions and ElevenLabs transcriptions.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CreateSalesSessionRequest(BaseModel):
    customer_id: str = Field(description="UUID of customer being onboarded")
    policy_id: Optional[str] = Field(default=None, description="UUID of policy discussed")
    policy_version_id: Optional[str] = Field(default=None, description="UUID of policy version discussed")
    registration_id: Optional[str] = Field(default=None, description="UUID of related registration if existing")
    audio_storage_ref: str = Field(min_length=5, description="Private Cloudinary asset reference for sales audio")
    audio_mime_type: str = Field(description="MIME type of recorded audio (e.g. audio/mpeg, audio/wav, audio/m4a)")
    audio_file_size_bytes: int = Field(gt=0, description="Audio file size in bytes")
    duration_seconds: Optional[int] = Field(default=None, ge=0, description="Recording length in seconds")
    audio_checksum: str = Field(min_length=64, max_length=64, description="SHA-256 cryptographic checksum of audio")
    customer_consent: bool = Field(default=False, description="Mandatory affirmative customer recording consent")
    consent_notes: Optional[str] = Field(default=None, max_length=1000, description="Consent verification notes")


class SalesSessionResponse(BaseModel):
    id: str
    customer_id: str
    agent_id: str
    policy_id: Optional[str] = None
    policy_version_id: Optional[str] = None
    registration_id: Optional[str] = None
    audio_storage_ref: str
    audio_mime_type: str
    audio_file_size_bytes: int
    duration_seconds: Optional[int] = None
    audio_checksum: str
    customer_consent: bool
    consent_timestamp: Optional[str] = None
    consent_notes: Optional[str] = None
    status: str
    detected_language: Optional[str] = None
    provider_model: Optional[str] = None
    error_category: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str
    updated_at: str


class TranscriptResponse(BaseModel):
    session_id: str
    status: str
    transcript: Optional[str] = None
    detected_language: Optional[str] = None
    word_segments: List[Dict[str, Any]] = Field(default_factory=list)
    speaker_diarization: List[Dict[str, Any]] = Field(default_factory=list)
    provider_model: Optional[str] = None
    created_at: str
    updated_at: str


class StartTranscriptionResponse(BaseModel):
    session_id: str
    status: str
    message: str
    transcript: Optional[str] = None
