import logging
from email.message import EmailMessage

import aiosmtplib
from aiosmtplib import SMTPAuthenticationError, SMTPException

from app.config import get_settings
from app.models.appeal import Appeal
from app.models.user import User
from app.services.notifications.base import NotificationChannel

logger = logging.getLogger(__name__)


class EmailNotifier(NotificationChannel):
    async def send(self, user: User, appeal: Appeal, topic_name: str) -> bool:
        settings = get_settings()
        if not settings.smtp_host or not settings.smtp_from:
            logger.warning(
                "SMTP not configured (smtp_host=%r, smtp_from=%r); skipping email to %s. "
                "Put SMTP_* in .env (not .env.example) and restart the server.",
                settings.smtp_host or None,
                settings.smtp_from or None,
                user.email,
            )
            return False

        subject = f"[Обратная связь] Новое обращение #{appeal.id}"
        body = (
            f"Поступило новое анонимное обращение.\n\n"
            f"ID: {appeal.id}\n"
            f"Тема: {topic_name}\n"
            f"Текст:\n{appeal.text}\n\n"
            f"Панель: {settings.public_base_url}/admin/appeals/{appeal.id}"
        )

        message = EmailMessage()
        message["From"] = settings.smtp_from
        message["To"] = user.email
        message["Subject"] = subject
        message.set_content(body)

        password = (settings.smtp_password or "").replace(" ", "")
        use_starttls = settings.smtp_port == 587 and settings.smtp_use_tls

        try:
            await aiosmtplib.send(
                message,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                username=settings.smtp_user or None,
                password=password or None,
                start_tls=use_starttls,
                use_tls=settings.smtp_port == 465,
                timeout=30,
            )
            logger.info("Email notification sent to %s", user.email)
            return True
        except SMTPAuthenticationError:
            logger.error(
                "SMTP login rejected for mailbox %s (recipient %s). "
                "For Gmail use an App Password from https://myaccount.google.com/apppasswords "
                "(16 characters), set SMTP_PASSWORD in .env, then restart uvicorn.",
                settings.smtp_user,
                user.email,
            )
            return False
        except SMTPException as exc:
            logger.error("SMTP error sending to %s: %s", user.email, exc)
            return False
        except Exception:
            logger.exception("Failed to send email to %s", user.email)
            return False
