import logging
from email.message import EmailMessage

import aiosmtplib

from app.config import get_settings
from app.models.appeal import Appeal
from app.models.user import User
from app.services.notifications.base import NotificationChannel

logger = logging.getLogger(__name__)
settings = get_settings()


class EmailNotifier(NotificationChannel):
    async def send(self, user: User, appeal: Appeal, topic_name: str) -> bool:
        if not settings.smtp_host or not settings.smtp_from:
            logger.warning("SMTP not configured; skipping email to %s", user.email)
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

        try:
            await aiosmtplib.send(
                message,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                username=settings.smtp_user or None,
                password=settings.smtp_password or None,
                start_tls=settings.smtp_use_tls,
            )
            return True
        except Exception:
            logger.exception("Failed to send email to %s", user.email)
            return False
