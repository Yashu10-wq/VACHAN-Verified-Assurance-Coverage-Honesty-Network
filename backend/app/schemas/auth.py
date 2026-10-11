"""
Pydantic validation schemas for authentication and identity endpoints.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

from app.core.security import AccountStatus, UserRole


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, description="Password must be at least 8 characters")
    full_name: str = Field(min_length=2, max_length=150)
    phone: Optional[str] = Field(default=None, max_length=50)
    role: UserRole = Field(description="Requested role: CUSTOMER, INSURANCE_AGENT, or APPROVAL_AUTHORITY")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class VerifyEmailRequest(BaseModel):
    token: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


class BootstrapAuthorityRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2)
    bootstrap_secret: str


class ApproveAccountRequest(BaseModel):
    user_id: str
    status: AccountStatus = Field(description="Must be ACTIVE or REJECTED")
    reason: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    phone: Optional[str] = None
    role: UserRole
    account_status: AccountStatus
    email_verified_at: Optional[str] = None
    created_at: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in_minutes: int
    refresh_token: str
    user: UserResponse
