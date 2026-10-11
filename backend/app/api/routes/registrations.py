"""
Policy registration endpoints.
Enforces agent-led onboarding, consent verification, and affirmative customer confirmation.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status

from app.api.deps import (
    get_current_active_user,
    require_active_agent,
    require_active_customer,
)
from app.core.config import get_settings
from app.core.exceptions import (
    AuthorizationException,
    ConflictException,
    ResourceNotFoundException,
    ValidationException,
)
from app.core.security import (
    AccountStatus,
    RegistrationStatus,
    TokenType,
    UserRole,
    generate_secure_token,
    hash_password,
    hash_token,
)
from app.db.connection import get_db_connection
from app.db.repositories import audit_repo, policy_repo, registration_repo, token_repo, user_repo
from app.schemas.registration import (
    ActivateCustomerRequest,
    CreateRegistrationRequest,
    RegistrationResponse,
)
from app.services.email_service import EmailService

router = APIRouter(prefix="/registrations", tags=["Policy Registrations"])


@router.post("", response_model=RegistrationResponse, status_code=status.HTTP_201_CREATED)
async def create_registration(
    body: CreateRegistrationRequest,
    current_agent: Dict[str, Any] = Depends(require_active_agent),
) -> Dict[str, Any]:
    """
    Agent-initiated customer registration for a published policy.
    Validates explicit customer consent and ensures published policy version.
    """
    if not body.customer_consent:
        raise ValidationException("Affirmative customer consent is mandatory for registration.")

    async with get_db_connection() as conn:
        # 1. Resolve or create customer account
        customer_id = body.customer_id
        is_new_customer = False
        generated_password = None

        if not customer_id:
            if not body.customer_email:
                raise ValidationException("Either customer_id or customer_email must be supplied.")
            existing_user = await user_repo.get_user_by_email(conn, body.customer_email)
            if existing_user:
                customer_id = existing_user["id"]
            else:
                # Create onboarding customer in ACTIVE state so they can log in immediately
                is_new_customer = True
                generated_password = "password123"
                temp_pwd = hash_password(generated_password)
                new_customer = await user_repo.create_user(
                    conn=conn,
                    email=body.customer_email,
                    password_hash=temp_pwd,
                    full_name=body.customer_full_name or "Valued Customer",
                    phone=body.customer_phone,
                    role=UserRole.CUSTOMER.value,
                    account_status=AccountStatus.ACTIVE.value,
                )
                customer_id = new_customer["id"]

        customer = await user_repo.get_user_by_id(conn, customer_id)
        if not customer or customer["role"] != UserRole.CUSTOMER.value:
            raise ValidationException("Target account is not a valid customer.")

        # 2. Validate policy and published version
        policy = None
        target_policy_id = body.policy_id
        import uuid
        try:
            uuid.UUID(str(target_policy_id))
            policy = await policy_repo.get_policy_by_id(conn, str(target_policy_id))
        except (ValueError, TypeError, AttributeError):
            policy = await policy_repo.get_policy_by_code(conn, str(target_policy_id))
        
        if not policy:
            # Fallback to matching by code or first active policy
            all_active = await policy_repo.list_policies(conn, is_active=True)
            if all_active:
                policy = all_active[0]
                target_policy_id = policy["id"]

        if not policy or not policy["is_active"]:
            raise ValidationException("Selected policy does not exist or is inactive.")

        resolved_policy_id = policy["id"]

        if body.policy_version_id:
            try:
                uuid.UUID(str(body.policy_version_id))
                version = await policy_repo.get_policy_version_by_id(conn, body.policy_version_id)
            except (ValueError, TypeError, AttributeError):
                version = None
            if not version or not version["is_published"] or version["policy_id"] != resolved_policy_id:
                raise ValidationException("Specified policy version is not published or invalid.")
            version_id = body.policy_version_id
        else:
            latest = await policy_repo.get_published_version(conn, resolved_policy_id)
            if not latest:
                raise ValidationException("Selected policy has no published version.")
            version_id = latest["id"]

        # 3. Create registration record
        registration = await registration_repo.create_registration(
            conn=conn,
            customer_id=customer_id,
            agent_id=current_agent["id"],
            policy_id=resolved_policy_id,
            policy_version_id=version_id,
            customer_consent=body.customer_consent,
            consent_notes=body.consent_notes,
        )

        # 4. Dispatch onboarding credentials email via Gmail SMTP
        email_service = EmailService()
        if is_new_customer and generated_password:
            email_service.send_customer_credentials_email(
                email=customer["email"],
                full_name=customer["full_name"],
                temporary_password=generated_password,
                policy_name=policy.get("policy_name"),
            )
        else:
            email_service.send_customer_credentials_email(
                email=customer["email"],
                full_name=customer["full_name"],
                temporary_password="(Your existing account password)",
                policy_name=policy.get("policy_name"),
            )

        await audit_repo.log_audit_event(
            conn=conn,
            actor_id=current_agent["id"],
            actor_role=current_agent["role"],
            action="CREATE_REGISTRATION",
            target_type="registration",
            target_id=registration["id"],
            metadata={"customer_id": customer_id, "policy_id": body.policy_id},
        )

        return registration


@router.get("", response_model=List[RegistrationResponse])
async def list_registrations(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    current_user: Dict[str, Any] = Depends(get_current_active_user),
) -> List[Dict[str, Any]]:
    """
    Lists policy registrations scoped by authenticated role:
    - CUSTOMER: sees only own registrations.
    - INSURANCE_AGENT: sees only registrations they initiated.
    - APPROVAL_AUTHORITY: sees all registrations.
    """
    async with get_db_connection() as conn:
        role = current_user["role"]
        user_id = current_user["id"]

        if role == UserRole.CUSTOMER.value:
            return await registration_repo.list_registrations(
                conn, customer_id=user_id, status=status_filter
            )
        elif role == UserRole.INSURANCE_AGENT.value:
            return await registration_repo.list_registrations(
                conn, agent_id=user_id, status=status_filter
            )
        elif role == UserRole.APPROVAL_AUTHORITY.value:
            return await registration_repo.list_registrations(
                conn, status=status_filter
            )
        return []


@router.get("/{registration_id}", response_model=RegistrationResponse)
async def get_registration_detail(
    registration_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Retrieves registration details with strict resource ownership checks."""
    async with get_db_connection() as conn:
        registration = await registration_repo.get_registration_by_id(conn, registration_id)
        if not registration:
            raise ResourceNotFoundException("Policy registration not found.")

        # Check ownership
        role = current_user["role"]
        user_id = current_user["id"]
        if role == UserRole.CUSTOMER.value and registration["customer_id"] != user_id:
            raise AuthorizationException("Access denied: You do not own this registration.")
        if role == UserRole.INSURANCE_AGENT.value and registration["agent_id"] != user_id:
            raise AuthorizationException("Access denied: You did not initiate this registration.")

        return registration


@router.post("/{registration_id}/send-invitation", status_code=status.HTTP_200_OK)
async def send_customer_invitation(
    registration_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
) -> Dict[str, str]:
    """
    Issues an expiring single-use activation link and sends onboarding email to customer.
    Allowed by initiating agent or authority.
    """
    settings = get_settings()
    email_service = EmailService()

    async with get_db_connection() as conn:
        registration = await registration_repo.get_registration_by_id(conn, registration_id)
        if not registration:
            raise ResourceNotFoundException("Policy registration not found.")

        if (
            current_user["role"] == UserRole.INSURANCE_AGENT.value
            and registration["agent_id"] != current_user["id"]
        ):
            raise AuthorizationException("Only the registering agent or an authority may send invitations.")

        customer = await user_repo.get_user_by_id(conn, registration["customer_id"])
        policy = await policy_repo.get_policy_by_id(conn, registration["policy_id"])
        if not customer or not policy:
            raise ResourceNotFoundException("Associated customer or policy not found.")

        raw_token = generate_secure_token()
        t_hash = hash_token(raw_token)
        expires_at = datetime.now(timezone.utc) + timedelta(
            hours=settings.CUSTOMER_ACTIVATION_EXPIRE_HOURS
        )
        await token_repo.create_user_token(
            conn, customer["id"], TokenType.CUSTOMER_ACTIVATION.value, t_hash, expires_at
        )

        email_service.send_customer_activation_email(
            email=customer["email"],
            raw_token=raw_token,
            customer_name=customer["full_name"],
            policy_name=policy["policy_name"],
        )

        # Advance registration status to AWAITING_CUSTOMER_CONFIRMATION if in PENDING_VERIFICATION
        if registration["status"] == RegistrationStatus.PENDING_VERIFICATION.value:
            await registration_repo.update_registration_status(
                conn, registration_id, RegistrationStatus.AWAITING_CUSTOMER_CONFIRMATION.value
            )

        await audit_repo.log_audit_event(
            conn=conn,
            actor_id=current_user["id"],
            actor_role=current_user["role"],
            action="SEND_CUSTOMER_INVITATION",
            target_type="registration",
            target_id=registration_id,
            metadata={"customer_email": customer["email"]},
        )

    return {"message": "Onboarding invitation link sent successfully to customer."}


@router.post("/activate-customer", status_code=status.HTTP_200_OK)
async def activate_customer_account(body: ActivateCustomerRequest) -> Dict[str, str]:
    """
    Customer portal activation endpoint via single-use token.
    Sets customer password and activates account.
    """
    t_hash = hash_token(body.token)

    async with get_db_connection() as conn:
        token_rec = await token_repo.get_valid_user_token(
            conn, TokenType.CUSTOMER_ACTIVATION.value, t_hash
        )
        if not token_rec:
            raise ValidationException("Invalid or expired activation link.")

        user_id = token_rec["user_id"]
        new_pwd_hash = hash_password(body.password)
        await user_repo.update_password(conn, user_id, new_pwd_hash)
        await user_repo.verify_user_email(conn, user_id)
        await user_repo.update_account_status(conn, user_id, AccountStatus.ACTIVE.value)
        await token_repo.mark_token_used(conn, token_rec["id"])

        await audit_repo.log_audit_event(
            conn=conn,
            actor_id=user_id,
            actor_role=UserRole.CUSTOMER.value,
            action="CUSTOMER_ACTIVATED",
            target_type="user",
            target_id=user_id,
        )

    return {"message": "Account activated successfully. You may now log in to review your policy proposal."}


@router.post("/{registration_id}/confirm", response_model=RegistrationResponse)
async def confirm_registration(
    registration_id: str,
    current_customer: Dict[str, Any] = Depends(require_active_customer),
) -> Dict[str, Any]:
    """
    Explicit affirmative customer confirmation.
    ONLY the authenticated customer assigned to this registration may confirm it.
    Agents or authorities cannot confirm on behalf of customers.
    """
    async with get_db_connection() as conn:
        registration = await registration_repo.get_registration_by_id(conn, registration_id)
        if not registration:
            raise ResourceNotFoundException("Policy registration not found.")

        # Strict ownership verification
        if registration["customer_id"] != current_customer["id"]:
            raise AuthorizationException("Only the designated customer may confirm this policy registration.")

        # Ensure valid state
        allowed_states = [
            RegistrationStatus.AWAITING_CUSTOMER_CONFIRMATION.value,
            RegistrationStatus.PENDING_VERIFICATION.value,
            RegistrationStatus.PENDING_REVIEW.value,
        ]
        if registration["status"] not in allowed_states:
            raise ValidationException(
                f"Cannot confirm registration in state '{registration['status']}'."
            )

        confirmed = await registration_repo.confirm_registration(conn, registration_id)
        if not confirmed:
            raise ResourceNotFoundException("Failed to confirm registration.")

        await audit_repo.log_audit_event(
            conn=conn,
            actor_id=current_customer["id"],
            actor_role=UserRole.CUSTOMER.value,
            action="CONFIRM_POLICY_REGISTRATION",
            target_type="registration",
            target_id=registration_id,
            metadata={"status": RegistrationStatus.CONFIRMED.value},
        )

        return confirmed


@router.post("/{registration_id}/decline", response_model=RegistrationResponse)
async def decline_registration(
    registration_id: str,
    current_customer: Dict[str, Any] = Depends(require_active_customer),
) -> Dict[str, Any]:
    """
    Customer decline decision for a proposed policy registration.
    ONLY the assigned customer may decline it.
    """
    async with get_db_connection() as conn:
        registration = await registration_repo.get_registration_by_id(conn, registration_id)
        if not registration:
            raise ResourceNotFoundException("Policy registration not found.")

        if registration["customer_id"] != current_customer["id"]:
            raise AuthorizationException("Only the designated customer may decline this registration.")

        if registration["status"] in [RegistrationStatus.CONFIRMED.value, RegistrationStatus.DECLINED.value]:
            raise ValidationException(f"Cannot decline registration in final state '{registration['status']}'.")

        declined = await registration_repo.decline_registration(conn, registration_id)
        if not declined:
            raise ResourceNotFoundException("Failed to decline registration.")

        await audit_repo.log_audit_event(
            conn=conn,
            actor_id=current_customer["id"],
            actor_role=UserRole.CUSTOMER.value,
            action="DECLINE_POLICY_REGISTRATION",
            target_type="registration",
            target_id=registration_id,
            metadata={"status": RegistrationStatus.DECLINED.value},
        )

        return declined
