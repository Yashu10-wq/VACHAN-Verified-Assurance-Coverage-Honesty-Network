"""
Pydantic validation schemas for insurance claims, evidence metadata,
assessments, and lifecycle status transitions.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

from app.core.security import (
    AssessmentOutcome,
    ClaimCategory,
    ClaimStatus,
    EvidenceType,
    RuleOutcome,
)


class CreateClaimRequest(BaseModel):
    registration_id: str = Field(description="UUID of active confirmed policy registration")
    claim_category: ClaimCategory = Field(description="VEHICLE, MEDICAL, or GENERIC")
    requested_amount: Decimal = Field(gt=0, description="Exact positive monetary claim amount")
    incident_date: date = Field(description="Date on which the insured incident occurred")
    description: str = Field(min_length=10, max_length=5000, description="Detailed account of the claim incident")
    structured_details: Dict[str, Any] = Field(default_factory=dict, description="Category-specific structured metadata")

    @field_validator("incident_date")
    @classmethod
    def validate_incident_date_not_future(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("Incident date cannot be in the future.")
        return v


class ClaimResponse(BaseModel):
    id: str
    customer_id: str
    registration_id: str
    policy_id: str
    policy_version_id: str
    claim_category: ClaimCategory
    requested_amount: str = Field(description="Exact decimal string representation")
    incident_date: str
    submission_timestamp: str
    description: str
    structured_details: Dict[str, Any]
    status: ClaimStatus
    created_at: str
    updated_at: str


class ClaimEvidenceResponse(BaseModel):
    id: str
    claim_id: str
    uploader_id: str
    evidence_type: str
    original_filename: str
    document_storage_ref: str
    file_size_bytes: int
    mime_type: str
    document_checksum: str
    analysis_status: str
    resource_metadata: Dict[str, Any]
    created_at: str


class RuleEvaluationResult(BaseModel):
    rule_id: str
    result: RuleOutcome
    explanation: str
    details: Dict[str, Any] = Field(default_factory=dict)


class ClaimAssessmentResponse(BaseModel):
    id: str
    claim_id: str
    policy_version_id: str
    assessment_version: int
    overall_outcome: AssessmentOutcome
    rules_evaluated: List[RuleEvaluationResult]
    requested_amount: str
    applicable_limit: str
    potentially_payable_amount: str
    excess_amount: str
    missing_evidence: List[str]
    review_flags: List[str]
    assessed_by: Optional[str] = None
    created_at: str


class ClaimStatusHistoryResponse(BaseModel):
    id: str
    claim_id: str
    actor_id: Optional[str] = None
    actor_role: str
    previous_status: str
    new_status: str
    reason: str
    decision_metadata: Dict[str, Any]
    audit_correlation_id: Optional[str] = None
    created_at: str


class ClaimDetailResponse(ClaimResponse):
    evidence: List[ClaimEvidenceResponse] = Field(default_factory=list)
    latest_assessment: Optional[ClaimAssessmentResponse] = None
    status_history: List[ClaimStatusHistoryResponse] = Field(default_factory=list)


class TransitionStatusRequest(BaseModel):
    target_status: ClaimStatus = Field(description="Desired new claim lifecycle state")
    reason: str = Field(min_length=5, max_length=2000, description="Mandatory audit explanation for the transition")
    decision_metadata: Dict[str, Any] = Field(default_factory=dict, description="Structured notes or decision parameters")


class DuplicateCandidateResponse(BaseModel):
    candidate_claim_id: str
    match_score: float
    match_reasons: List[str]
    claim_status: str
    incident_date: str
    requested_amount: str
    claim_category: str


class DuplicateCandidatesListResponse(BaseModel):
    claim_id: str
    total_candidates: int
    candidates: List[DuplicateCandidateResponse]


class SignedUrlResponse(BaseModel):
    evidence_id: str
    signed_url: str
    expires_in_seconds: int
