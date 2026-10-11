"""
FastAPI dependency injection utilities for authentication, role verification, and database sessions.
"""

from typing import Any, Callable, Dict, List
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.exceptions import AuthenticationException, AuthorizationException
from app.core.security import AccountStatus, UserRole, decode_access_token
from app.db.connection import get_db_connection
from app.db.repositories import user_repo

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    Validates JWT access token and retrieves current user from database.
    Does not trust any client-supplied role or user ID.
    """
    if not token:
        raise AuthenticationException("Authentication credentials are required.")

    payload = decode_access_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationException("Invalid token payload: missing subject.")

    async with get_db_connection() as conn:
        user = await user_repo.get_user_by_id(conn, user_id)
        if not user:
            raise AuthenticationException("User account not found.")
        return user


async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Ensures current user has an ACTIVE account status."""
    acc_status = current_user.get("account_status")
    if acc_status == AccountStatus.PENDING_VERIFICATION.value:
        raise AuthorizationException("Account requires email verification before access is granted.")
    if acc_status == AccountStatus.PENDING_APPROVAL.value:
        raise AuthorizationException("Account is pending approval by an authority administrator.")
    if acc_status in [AccountStatus.REJECTED.value, AccountStatus.SUSPENDED.value]:
        raise AuthorizationException(f"Account access is disabled ({acc_status}).")
    if acc_status != AccountStatus.ACTIVE.value:
        raise AuthorizationException("Account is not active.")

    return current_user


def require_roles(*allowed_roles: UserRole) -> Callable:
    """Dependency factory checking that active user holds one of the specified roles."""

    async def role_checker(
        current_user: Dict[str, Any] = Depends(get_current_active_user)
    ) -> Dict[str, Any]:
        user_role = current_user.get("role")
        allowed_values = [r.value for r in allowed_roles]
        if user_role not in allowed_values:
            raise AuthorizationException(
                f"Role '{user_role}' is not authorized for this operation. "
                f"Required role(s): {', '.join(allowed_values)}."
            )
        return current_user

    return role_checker


# Role-specific convenience dependencies
require_active_authority = require_roles(UserRole.APPROVAL_AUTHORITY)
require_active_agent = require_roles(UserRole.INSURANCE_AGENT)
require_active_customer = require_roles(UserRole.CUSTOMER)
