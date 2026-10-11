"""
Pydantic validation schemas for insurance policies and versions.
"""

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.core.security import PolicyCategory


class CreatePolicyRequest(BaseModel):
    insurer_name: str = Field(min_length=2, max_length=200)
    policy_name: str = Field(min_length=2, max_length=200)
    policy_code: str = Field(min_length=3, max_length=64)
    category: PolicyCategory
    description: str = Field(min_length=10)
    coverage_limit: Decimal = Field(gt=0, description="Exact numeric coverage limit")
    waiting_period_days: int = Field(default=0, ge=0)
    claim_filing_window_days: int = Field(default=30, gt=0)


class CreatePolicyVersionRequest(BaseModel):
    version_number: int = Field(gt=0)
    document_storage_ref: str = Field(min_length=5, description="Cloudinary or secure off-chain storage reference")
    document_checksum: str = Field(min_length=64, max_length=64, description="SHA-256 checksum of policy document")
    effective_date: date
    expiry_date: Optional[date] = None
    terms_json: Optional[Dict[str, Any]] = None


class PolicyVersionResponse(BaseModel):
    id: str
    policy_id: str
    version_number: int
    document_storage_ref: str
    document_checksum: str
    effective_date: str
    expiry_date: Optional[str] = None
    terms_json: Dict[str, Any]
    is_published: bool
    published_at: Optional[str] = None
    published_by: Optional[str] = None
    created_at: Optional[str] = None


class PolicyResponse(BaseModel):
    id: str
    insurer_name: str
    policy_name: str
    policy_code: str
    category: PolicyCategory
    description: str
    coverage_limit: float
    waiting_period_days: int
    claim_filing_window_days: int
    is_active: bool
    created_by: Optional[str] = None
    created_at: Optional[str] = None
    latest_version: Optional[PolicyVersionResponse] = None
