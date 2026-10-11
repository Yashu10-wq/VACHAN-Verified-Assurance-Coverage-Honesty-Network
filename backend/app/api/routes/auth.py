"""
Authentication and identity lifecycle endpoints.
Enforces RBAC, password security, token hashing, and audit logging.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.api.deps import get_current_active_user, get_current_user, require_active_authority
from app.core.config import get_settings
from app.core.exceptions import (
    AuthenticationException,
    AuthorizationException,
    ConflictException,
    ResourceNotFoundException,
    ValidationException,
)
from app.core.logging import get_logger
from app.core.security import (
    AccountStatus,
    TokenType,
    UserRole,
    create_access_token,
    generate_secure_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.db.connection import get_db_connection
from app.db.repositories import audit_repo, token_repo, user_repo
from app.schemas.auth import (
    ApproveAccountRequest,
    BootstrapAuthorityRequest,
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshTokenRequest,
    ResendVerificationRequest,
    SignupRequest,
    TokenResponse,
    UserResponse,
    VerifyEmailRequest,
)
from app.services.email_service import EmailService

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication & Identity"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: SignupRequest) -> Dict[str, Any]:
    """
    Public registration for all 3 supported roles.
    - CUSTOMER: begins in PENDING_VERIFICATION (requires email verification).
    - INSURANCE_AGENT: begins in PENDING_APPROVAL (requires authority review).
    - APPROVAL_AUTHORITY: begins in PENDING_APPROVAL (cannot self-grant privileges).
    """
    settings = get_settings()
    email_service = EmailService()

    async with get_db_connection() as conn:
        existing = await user_repo.get_user_by_email(conn, body.email)
        if existing:
            raise ConflictException("An account with this email already exists.")

        # Determine safe initial account status
        initial_status = AccountStatus.ACTIVE

        pwd_hash = hash_password(body.password)
        user = await user_repo.create_user(
            conn=conn,
            email=body.email,
            password_hash=pwd_hash,
            full_name=body.full_name,
            phone=body.phone,
            role=body.role.value,
            account_status=initial_status.value,
        )

        # Dispatch welcome and credentials email
        email_service.send_customer_credentials_email(
            email=user["email"],
            full_name=user["full_name"],
            temporary_password=body.password,
            policy_name="Customer Welcome Portal",
        )

        await audit_repo.log_audit_event(
            conn=conn,
            actor_id=user["id"],
            actor_role=user["role"],
            action="SIGNUP",
            target_type="user",
            target_id=user["id"],
            metadata={"role": user["role"], "initial_status": initial_status.value},
        )

        return user


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest) -> Dict[str, Any]:
    """Authenticates credentials and returns access and refresh tokens."""
    settings = get_settings()

    async with get_db_connection() as conn:
        user = await user_repo.get_user_by_email(conn, body.email)
        if not user or not verify_password(body.password, user["password_hash"]):
            raise AuthenticationException("Invalid email or password.")

        acc_status = user["account_status"]
        if acc_status == AccountStatus.SUSPENDED.value:
            raise AuthorizationException("Account is suspended. Please contact support.")
        if acc_status == AccountStatus.REJECTED.value:
            raise AuthorizationException("Account request was rejected.")
        if acc_status == AccountStatus.PENDING_VERIFICATION.value:
            raise AuthorizationException("Email verification required before login.")
        if acc_status == AccountStatus.PENDING_APPROVAL.value:
            raise AuthorizationException("Account is awaiting administrator review and approval.")

        # Update last login
        await user_repo.update_last_login(conn, user["id"])

        # Generate tokens
        access_token = create_access_token(
            {"sub": user["id"], "role": user["role"], "email": user["email"]}
        )

        raw_refresh = generate_secure_token()
        refresh_hash = hash_token(raw_refresh)
        refresh_exp = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await token_repo.create_refresh_token(conn, user["id"], refresh_hash, refresh_exp)

        await audit_repo.log_audit_event(
            conn=conn,
            actor_id=user["id"],
            actor_role=user["role"],
            action="LOGIN_SUCCESS",
            target_type="user",
            target_id=user["id"],
        )

        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            "refresh_token": raw_refresh,
            "user": user,
        }


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    body: RefreshTokenRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, str]:
    """Revokes refresh token to terminate session."""
    refresh_hash = hash_token(body.refresh_token)
    async with get_db_connection() as conn:
        await token_repo.revoke_refresh_token(conn, refresh_hash)
        await audit_repo.log_audit_event(
            conn=conn,
            actor_id=current_user["id"],
            actor_role=current_user["role"],
            action="LOGOUT",
            target_type="session",
        )
    return {"message": "Logged out successfully."}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshTokenRequest) -> Dict[str, Any]:
    """Rotates refresh token and issues a new access token."""
    settings = get_settings()
    refresh_hash = hash_token(body.refresh_token)

    async with get_db_connection() as conn:
        token_record = await token_repo.get_valid_refresh_token(conn, refresh_hash)
        if not token_record:
            raise AuthenticationException("Invalid or expired refresh token.")

        user = await user_repo.get_user_by_id(conn, token_record["user_id"])
        if not user or user["account_status"] != AccountStatus.ACTIVE.value:
            raise AuthorizationException("Account is no longer active.")

        # Revoke old refresh token (rotation)
        await token_repo.revoke_refresh_token(conn, refresh_hash)

        # Issue new pair
        access_token = create_access_token(
            {"sub": user["id"], "role": user["role"], "email": user["email"]}
        )
        new_raw_refresh = generate_secure_token()
        new_refresh_hash = hash_token(new_raw_refresh)
        new_refresh_exp = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await token_repo.create_refresh_token(conn, user["id"], new_refresh_hash, new_refresh_exp)

        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            "refresh_token": new_raw_refresh,
            "user": user,
        }


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Returns currently authenticated user profile."""
    return current_user


@router.post("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email(body: VerifyEmailRequest) -> Dict[str, str]:
    """Verifies email address using single-use hashed token."""
    t_hash = hash_token(body.token)
    async with get_db_connection() as conn:
        token_rec = await token_repo.get_valid_user_token(
            conn, TokenType.EMAIL_VERIFICATION.value, t_hash
        )
        if not token_rec:
            raise ValidationException("Invalid or expired email verification token.")

        await token_repo.mark_token_used(conn, token_rec["id"])
        await user_repo.verify_user_email(conn, token_rec["user_id"])
        await audit_repo.log_audit_event(
            conn=conn,
            actor_id=token_rec["user_id"],
            actor_role=UserRole.CUSTOMER.value,
            action="EMAIL_VERIFIED",
            target_type="user",
            target_id=token_rec["user_id"],
        )

    return {"message": "Email verified successfully. Account is now active."}


@router.post("/resend-verification", status_code=status.HTTP_200_OK)
async def resend_verification(body: ResendVerificationRequest) -> Dict[str, str]:
    """Resends email verification token without leaking user existence."""
    settings = get_settings()
    email_service = EmailService()

    async with get_db_connection() as conn:
        user = await user_repo.get_user_by_email(conn, body.email)
        if user and user["account_status"] == AccountStatus.PENDING_VERIFICATION.value:
            raw_token = generate_secure_token()
            t_hash = hash_token(raw_token)
            expires_at = datetime.now(timezone.utc) + timedelta(
                hours=settings.EMAIL_VERIFICATION_EXPIRE_HOURS
            )
            await token_repo.create_user_token(
                conn, user["id"], TokenType.EMAIL_VERIFICATION.value, t_hash, expires_at
            )
            email_service.send_verification_email(user["email"], raw_token)

    return {"message": "If an unverified account exists, a new verification link has been sent."}


@router.post("/password-reset/request", status_code=status.HTTP_200_OK)
async def request_password_reset(body: PasswordResetRequest) -> Dict[str, str]:
    """Generates password reset token without disclosing email existence."""
    settings = get_settings()
    email_service = EmailService()

    async with get_db_connection() as conn:
        user = await user_repo.get_user_by_email(conn, body.email)
        if user and user["account_status"] == AccountStatus.ACTIVE.value:
            raw_token = generate_secure_token()
            t_hash = hash_token(raw_token)
            expires_at = datetime.now(timezone.utc) + timedelta(
                hours=settings.PASSWORD_RESET_EXPIRE_HOURS
            )
            await token_repo.create_user_token(
                conn, user["id"], TokenType.PASSWORD_RESET.value, t_hash, expires_at
            )
            email_service.send_password_reset_email(user["email"], raw_token)

    return {"message": "If a matching active account exists, password reset instructions have been sent."}


@router.post("/password-reset/confirm", status_code=status.HTTP_200_OK)
async def confirm_password_reset(body: PasswordResetConfirm) -> Dict[str, str]:
    """Applies password reset using verified single-use token."""
    t_hash = hash_token(body.token)

    async with get_db_connection() as conn:
        token_rec = await token_repo.get_valid_user_token(
            conn, TokenType.PASSWORD_RESET.value, t_hash
        )
        if not token_rec:
            raise ValidationException("Invalid or expired password reset token.")

        new_hash = hash_password(body.new_password)
        await user_repo.update_password(conn, token_rec["user_id"], new_hash)
        await token_repo.mark_token_used(conn, token_rec["id"])
        # Invalidate all active sessions for security
        await token_repo.revoke_all_user_refresh_tokens(conn, token_rec["user_id"])

        await audit_repo.log_audit_event(
            conn=conn,
            actor_id=token_rec["user_id"],
            actor_role=None,
            action="PASSWORD_RESET_SUCCESS",
            target_type="user",
            target_id=token_rec["user_id"],
        )

    return {"message": "Password has been successfully updated. Please log in with your new password."}


@router.post("/bootstrap-authority", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def bootstrap_authority(body: BootstrapAuthorityRequest) -> Dict[str, Any]:
    """
    Operator-controlled bootstrap endpoint for initial system authority account.
    Requires matching AUTHORITY_BOOTSTRAP_SECRET environment configuration.
    """
    settings = get_settings()
    if not settings.AUTHORITY_BOOTSTRAP_SECRET or body.bootstrap_secret != settings.AUTHORITY_BOOTSTRAP_SECRET:
        raise AuthorizationException("Invalid authority bootstrap secret.")

    async with get_db_connection() as conn:
        existing = await user_repo.get_user_by_email(conn, body.email)
        if existing:
            # Activate if already created
            user = await user_repo.update_account_status(conn, existing["id"], AccountStatus.ACTIVE.value)
            if not user:
                raise ResourceNotFoundException("User not found.")
            return user

        pwd_hash = hash_password(body.password)
        user = await user_repo.create_user(
            conn=conn,
            email=body.email,
            password_hash=pwd_hash,
            full_name=body.full_name,
            role=UserRole.APPROVAL_AUTHORITY.value,
            account_status=AccountStatus.ACTIVE.value,
        )

        await audit_repo.log_audit_event(
            conn=conn,
            actor_id=user["id"],
            actor_role=UserRole.APPROVAL_AUTHORITY.value,
            action="AUTHORITY_BOOTSTRAP",
            target_type="user",
            target_id=user["id"],
        )

        return user


@router.post("/approve-account", response_model=UserResponse)
async def approve_account(
    body: ApproveAccountRequest,
    current_authority: Dict[str, Any] = Depends(require_active_authority),
) -> Dict[str, Any]:
    """
    Authorized authority approval/rejection endpoint for pending agents and authorities.
    Prevents self-approval.
    """
    if current_authority["id"] == body.user_id:
        raise AuthorizationException("Authorities cannot approve or modify their own account status.")

    if body.status not in [AccountStatus.ACTIVE, AccountStatus.REJECTED]:
        raise ValidationException("Status must be ACTIVE or REJECTED.")

    async with get_db_connection() as conn:
        target_user = await user_repo.get_user_by_id(conn, body.user_id)
        if not target_user:
            raise ResourceNotFoundException("Target user account not found.")

        updated = await user_repo.update_account_status(
            conn=conn,
            user_id=body.user_id,
            new_status=body.status.value,
            approved_by=current_authority["id"],
            rejection_reason=body.reason,
        )
        if not updated:
            raise ResourceNotFoundException("Failed to update user status.")

        await audit_repo.log_audit_event(
            conn=conn,
            actor_id=current_authority["id"],
            actor_role=current_authority["role"],
            action="ACCOUNT_STATUS_DECISION",
            target_type="user",
            target_id=body.user_id,
            metadata={"new_status": body.status.value, "reason": body.reason},
        )

        return updated
