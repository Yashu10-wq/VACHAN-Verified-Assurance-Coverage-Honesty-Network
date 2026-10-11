"""
Email service abstraction for InsureChain VoiceGuard.
Supports console, test in-memory recording, and SMTP delivery.
Never prints raw credentials or secret values.
"""

from dataclasses import dataclass
from typing import List, Optional
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SentMessage:
    to_email: str
    subject: str
    body_text: str
    token: str


class EmailService:
    """Service handling transactional emails (verification, reset, customer invitation)."""

    # In-memory store for unit test assertions
    sent_messages: List[SentMessage] = []

    def __init__(self) -> None:
        self.settings = get_settings()

    def send_verification_email(self, email: str, raw_token: str) -> bool:
        """Sends email verification link."""
        link = f"{self.settings.APP_URL}/verify-email?token={raw_token}"
        subject = f"Verify your {self.settings.APP_NAME} account"
        body = (
            f"Welcome to InsureChain VoiceGuard!\n\n"
            f"Please verify your email address by visiting the following link:\n"
            f"{link}\n\n"
            f"This single-use link expires in {self.settings.EMAIL_VERIFICATION_EXPIRE_HOURS} hours.\n"
        )
        return self._deliver(to_email=email, subject=subject, body=body, token=raw_token)

    def send_password_reset_email(self, email: str, raw_token: str) -> bool:
        """Sends password reset link."""
        link = f"{self.settings.APP_URL}/reset-password?token={raw_token}"
        subject = f"Password Reset for {self.settings.APP_NAME}"
        body = (
            f"We received a request to reset your password.\n\n"
            f"Reset your password by visiting the following link:\n"
            f"{link}\n\n"
            f"This single-use link expires in {self.settings.PASSWORD_RESET_EXPIRE_HOURS} hour.\n"
            f"If you did not request this, you can safely ignore this email.\n"
        )
        return self._deliver(to_email=email, subject=subject, body=body, token=raw_token)

    def send_customer_activation_email(
        self, email: str, raw_token: str, customer_name: str, policy_name: str
    ) -> bool:
        """Sends secure onboarding activation link to customer."""
        link = f"{self.settings.APP_URL}/activate?token={raw_token}"
        subject = f"Action Required: Review your policy proposal for {policy_name}"
        body = (
            f"Dear {customer_name},\n\n"
            f"An insurance agent has registered a proposed policy ({policy_name}) on your behalf.\n\n"
            f"To review the sales transcript, compare promised terms against actual policy clauses, "
            f"and set up your secure account, please visit:\n"
            f"{link}\n\n"
            f"This single-use link expires in {self.settings.CUSTOMER_ACTIVATION_EXPIRE_HOURS} hours.\n"
        )
        return self._deliver(to_email=email, subject=subject, body=body, token=raw_token)

    def _deliver(self, to_email: str, subject: str, body: str, token: str) -> bool:
        """Delivers message using configured provider."""
        provider = self.settings.EMAIL_PROVIDER.lower()

        # Always record in sent_messages for test observability
        self.sent_messages.append(
            SentMessage(to_email=to_email, subject=subject, body_text=body, token=token)
        )

        if provider == "test":
            logger.info("Test email recorded for %s (Subject: %s)", to_email, subject)
            return True

        if provider == "smtp" and self.settings.SMTP_HOST:
            try:
                msg = MIMEMultipart()
                msg["From"] = self.settings.EMAIL_FROM
                msg["To"] = to_email
                msg["Subject"] = subject
                msg.attach(MIMEText(body, "plain"))

                with smtplib.SMTP(
                    self.settings.SMTP_HOST, self.settings.SMTP_PORT, timeout=10
                ) as server:
                    if self.settings.SMTP_USERNAME and self.settings.SMTP_PASSWORD:
                        server.starttls()
                        server.login(self.settings.SMTP_USERNAME, self.settings.SMTP_PASSWORD)
                    server.send_message(msg)
                logger.info("SMTP email delivered to %s", to_email)
                return True
            except Exception as exc:
                logger.error("SMTP delivery failed to %s: %s", to_email, type(exc).__name__)
                return False

        # Default fallback: console output
        logger.info(
            "[EMAIL SERVICE - CONSOLE ADAPTER]\nTo: %s\nSubject: %s\n%s",
            to_email,
            subject,
            body,
        )
        return True
