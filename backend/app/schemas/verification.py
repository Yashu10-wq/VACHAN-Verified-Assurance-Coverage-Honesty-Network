"""
Pydantic validation schemas for Policy Document Extraction and
Gemini Policy-Promise Verification in InsureChain VoiceGuard.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PromiseVerdict(str, Enum):
    """The 5 grounded classifications for an agent's sales promise against policy terms."""
    SUPPORTED = "SUPPORTED"
    PARTLY_TRUE = "PARTLY_TRUE"
    CONTRADICTED = "CONTRADICTED"
    NOT_IN_POLICY = "NOT_IN_POLICY"
    UNCLEAR = "UNCLEAR"


class OverallIntegrityStatus(str, Enum):
    """High-level policy compliance assessment of the sales conversation."""
    VERIFIED = "VERIFIED"
    DISCREPANCIES_FOUND = "DISCREPANCIES_FOUND"
    MISLEADING_CLAIMS_DETECTED = "MISLEADING_CLAIMS_DETECTED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class VerificationStatus(str, Enum):
    """Lifecycle status of the verification job."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class ExtractionStatus(str, Enum):
    """Lifecycle status of policy document PDF text extraction."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class ValidationStatus(str, Enum):
    """Grounding verification status of quoted evidence."""
    GROUNDED = "GROUNDED"
    INVALID_QUOTE = "INVALID_QUOTE"
    UNVERIFIED_CITATION = "UNVERIFIED_CITATION"
    PARTIAL_MATCH = "PARTIAL_MATCH"


class PageExtractionItem(BaseModel):
    """Extracted text snippet from an individual PDF page."""
    page_number: int
    text: str
    section_headings: List[str] = []


class FindingItem(BaseModel):
    """A grounded verification finding matching an agent promise against policy terms."""
    finding_id: str = Field(description="Unique identifier for this finding")
    promise_text: str = Field(description="Agent's sales statement or commitment")
    transcript_quote: str = Field(description="Exact verbatim excerpt from the recorded transcript")
    speaker_label: Optional[str] = Field(default=None, description="Identified speaker in transcript")
    classification: PromiseVerdict = Field(description="Grounded comparison classification")
    policy_excerpt: Optional[str] = Field(default=None, description="Exact cited excerpt from policy text")
    page_number: Optional[int] = Field(default=None, description="Page number of cited policy clause")
    section_heading: Optional[str] = Field(default=None, description="Policy section header or clause title")
    explanation: str = Field(description="Clear explanation comparing the promise to policy reality")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Model certainty score")
    review_required: bool = Field(default=False, description="Flagged for manual operator review")
    review_reason: Optional[str] = Field(default=None, description="Reason why manual review is triggered")
    validation_status: ValidationStatus = Field(default=ValidationStatus.GROUNDED, description="Grounding validation status")


class VerificationReportResponse(BaseModel):
    """Complete verification report response."""
    id: str
    sales_session_id: str
    customer_id: str
    agent_id: str
    policy_id: str
    policy_version_id: str
    transcript_checksum: str
    report_version: int
    status: VerificationStatus
    model_identifier: str
    summary: Optional[str] = None
    overall_integrity_status: Optional[OverallIntegrityStatus] = None
    findings: List[FindingItem] = []
    supported_count: int = 0
    partly_true_count: int = 0
    contradicted_count: int = 0
    not_in_policy_count: int = 0
    unclear_count: int = 0
    review_flags: List[str] = []
    error_message: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class StartVerificationResponse(BaseModel):
    """Acknowledgment when a verification run is initiated."""
    session_id: str
    report_id: str
    report_version: int
    status: str
    message: str


class ReanalyzeRequest(BaseModel):
    """Optional payload when requesting a fresh re-analysis."""
    reason: Optional[str] = Field(default=None, description="Optional operational justification")


class PolicyExtractionResponse(BaseModel):
    """Extracted text metadata for a policy version."""
    id: str
    policy_version_id: str
    document_checksum: str
    status: ExtractionStatus
    page_count: int
    extracted_text_preview: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[str] = None
