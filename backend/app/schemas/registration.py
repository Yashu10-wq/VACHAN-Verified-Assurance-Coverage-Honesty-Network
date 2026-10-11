"""
Pydantic validation schemas for agent customer registrations and customer confirmation.
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field

from app.core.security import RegistrationStatus


class CreateRegistrationRequest(BaseModel):
    customer_id: Optional[str] = Field(default=None, description="Existing customer UUID if registered")
    customer_email: Optional[EmailStr] = Field(default=None, description="New customer email if onboarding")
    customer_full_name: Optional[str] = Field(default=None, description="Customer name if creating new account")
    customer_phone: Optional[str] = None
    policy_id: str
    policy_version_id: Optional[str] = Field(default=None, description="Version UUID, or uses latest published version")
    customer_consent: bool = Field(default=True, description="Must have affirmative customer consent")
    consent_notes: Optional[str] = None


class ActivateCustomerRequest(BaseModel):
    token: str
    password: str = Field(min_length=8)
    full_name: Optional[str] = None


class RegistrationResponse(BaseModel):
    id: str
    customer_id: str
    agent_id: str
    policy_id: str
    policy_version_id: str
    status: RegistrationStatus
    customer_consent: bool
    consent_timestamp: Optional[str] = None
    consent_notes: Optional[str] = None
    customer_decision_at: Optional[str] = None
    activated_at: Optional[str] = None
    declined_at: Optional[str] = None
    cancelled_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
