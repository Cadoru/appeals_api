import logging

import httpx

from app.config import get_settings
from app.models.appeal import Appeal
from app.models.user import User
from app.services.notifications.base import NotificationChannel

logger = logging.getLogger(__name__)
settings = get_settings()


class TelegramNotifier(NotificationChannel):
    async def send(self, user: User, appeal: Appeal, topic_name: str) -> bool:
        if not settings.telegram_bot_token or not user.telegram_chat_id:
            return False

        text = (
            f"<b>Новое обращение #{appeal.id}</b>\n"
            f"<b>Тема:</b> {topic_name}\n"
            f"<b>Текст:</b>\n{appeal.text[:3500]}"
        )
        url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
        payload = {
            "chat_id": user.telegram_chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
            return True
        except Exception:
            logger.exception("Failed to send Telegram to user %s", user.id)
            return False
