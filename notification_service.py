"""
notification_service.py - Gmail-only appointment alert system.

Sends email via Gmail SMTP (TLS on port 587) whenever a slot is found.
Retries up to 3 times on transient network failures before giving up.
"""

import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import config
from utils.logger import get_logger

logger = get_logger("notification_service")

# Maximum send attempts before giving up on a single notification
_MAX_RETRIES = 3
_RETRY_DELAY = 10  # seconds between retries


class NotificationService:
    """Gmail-only notification service for VFS appointment alerts."""

    # ── Public API ────────────────────────────────────────────────────────────

    def send_all(self, title: str, message: str) -> None:
        """Send notification (Gmail only)."""
        self.notify_email(subject=title, body=message)

    def appointment_found(self, location: str) -> None:
        """Send the standard 'slot found' alert for a given city."""
        subject = "🚨 VFS Appointment Slot Alert"
        body = (
            f"🚨 Appointment Slot Found!\n\n"
            f"Service : {config.VFS_COUNTRY} — {config.VFS_SERVICE}\n"
            f"Location: {location}\n\n"
            "Please visit the VFS Global website immediately to book your appointment:\n"
            f"{config.VFS_BOOKING_URL}\n\n"
            "Do not delay — slots fill up very quickly!"
        )
        logger.info("Sending appointment-found email for %s.", location)
        self.notify_email(subject=subject, body=body)

    # ── Gmail SMTP ────────────────────────────────────────────────────────────

    def notify_email(self, subject: str, body: str) -> bool:
        """
        Send an email via Gmail SMTP with retry logic.
        Returns True if the email was delivered, False after all retries fail.
        """
        sender   = config.EMAIL_SENDER
        password = config.EMAIL_APP_PASSWORD
        receiver = config.EMAIL_RECEIVER

        if not sender or not password or not receiver:
            logger.warning(
                "Email not configured — set EMAIL_SENDER, EMAIL_APP_PASSWORD, "
                "and EMAIL_RECEIVER in your .env file."
            )
            return False

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"]    = f"VFS Bot <{sender}>"
                msg["To"]      = receiver

                # Plain-text body
                msg.attach(MIMEText(body, "plain", "utf-8"))

                with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=30) as server:
                    server.ehlo()
                    server.starttls()
                    server.ehlo()
                    server.login(sender, password)
                    server.sendmail(sender, receiver, msg.as_string())

                logger.info(
                    "✅ Email sent to %s (attempt %d/%d).",
                    receiver, attempt, _MAX_RETRIES,
                )
                return True

            except smtplib.SMTPAuthenticationError as exc:
                # Auth failure is permanent — no point retrying
                logger.error(
                    "Email authentication failed. Check EMAIL_APP_PASSWORD "
                    "in .env (must be a Gmail App Password, not your account password). "
                    "Error: %s", exc,
                )
                return False

            except (smtplib.SMTPException, OSError, TimeoutError) as exc:
                logger.warning(
                    "Email attempt %d/%d failed: %s", attempt, _MAX_RETRIES, exc
                )
                if attempt < _MAX_RETRIES:
                    logger.info("Retrying email in %d seconds…", _RETRY_DELAY)
                    time.sleep(_RETRY_DELAY)
                else:
                    logger.error(
                        "All %d email attempts failed. Notification not delivered.",
                        _MAX_RETRIES,
                    )
                    return False

        return False

    def test_email(self) -> bool:
        """
        Send a test email to verify configuration.
        Call this once at startup to confirm email is working.
        """
        logger.info("Sending test email to verify configuration…")
        return self.notify_email(
            subject="VFS Bot — Email Test",
            body=(
                "✅ Your VFS appointment bot email notifications are working correctly.\n\n"
                f"Monitoring: {', '.join(config.CITIES)}\n"
                f"Service   : {config.VFS_COUNTRY} — {config.VFS_SERVICE}\n\n"
                "You will receive an email like this when a slot is detected."
            ),
        )
