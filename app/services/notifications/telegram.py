import html
import logging

import httpx

from app.config import get_settings
from app.models.appeal import Appeal
from app.models.user import User
from app.services.notifications.base import NotificationChannel

logger = logging.getLogger(__name__)


class TelegramNotifier(NotificationChannel):
    async def send(self, user: User, appeal: Appeal, topic_name: str) -> bool:
        settings = get_settings()

        if not settings.telegram_bot_token:
            logger.warning(
                "TELEGRAM_BOT_TOKEN is empty; skipping Telegram for user %s. "
                "Create a .env file (copy from .env.example) and restart the server.",
                user.id,
            )
            return False

        if not user.telegram_chat_id:
            logger.warning("telegram_chat_id is empty for user %s; skipping Telegram", user.id)
            return False

        if not user.notify_telegram:
            logger.debug("notify_telegram is disabled for user %s; skipping", user.id)
            return False

        safe_topic = html.escape(topic_name)
        safe_text = html.escape(appeal.text[:3500])
        text = (
            f"<b>Новое обращение #{appeal.id}</b>\n"
            f"<b>Тема:</b> {safe_topic}\n"
            f"<b>Текст:</b>\n{safe_text}"
        )
        url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
        payload = {
            "chat_id": user.telegram_chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }

        try:
            # trust_env=False: ignore system HTTP/SOCKS proxy (often breaks api.telegram.org)
            async with httpx.AsyncClient(timeout=15.0, trust_env=False) as client:
                response = await client.post(url, json=payload)
                if response.is_error:
                    logger.error(
                        "Telegram API error for user %s (chat_id=%s): %s %s",
                        user.id,
                        user.telegram_chat_id,
                        response.status_code,
                        response.text,
                    )
                    return False
            logger.info("Telegram notification sent to user %s (chat_id=%s)", user.id, user.telegram_chat_id)
            return True
        except Exception:
            logger.exception("Failed to send Telegram to user %s (chat_id=%s)", user.id, user.telegram_chat_id)
            return False
