import html
import logging

import httpx

from app.config import get_settings
from app.models.appeal import Appeal
from app.models.user import User
from app.services.notifications.base import NotificationChannel
from app.services.notifications.helpers import appeal_portal_url, attachments_summary, collect_attachment_files

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

        safe_topic = html.escape(topic_name)
        safe_text = html.escape(appeal.text[:3500])
        portal_link = html.escape(appeal_portal_url(appeal.id))
        attach_info = html.escape(attachments_summary(appeal).strip())

        text = (
            f"<b>Новое обращение #{appeal.id}</b>\n"
            f"<b>Тема:</b> {safe_topic}\n"
            f"<b>Текст:</b>\n{safe_text}"
        )
        if attach_info:
            text += f"\n<b>{attach_info}</b>"
        text += f"\n\n<a href=\"{portal_link}\">Открыть в портале</a>"

        base_url = f"https://api.telegram.org/bot{settings.telegram_bot_token}"
        chat_id = user.telegram_chat_id

        try:
            async with httpx.AsyncClient(timeout=60.0, trust_env=False) as client:
                response = await client.post(
                    f"{base_url}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": text,
                        "parse_mode": "HTML",
                        "disable_web_page_preview": False,
                    },
                )
                if response.is_error:
                    logger.error(
                        "Telegram sendMessage error for user %s: %s %s",
                        user.id,
                        response.status_code,
                        response.text,
                    )
                    return False

                files_sent = 0
                for path, filename, content_type in collect_attachment_files(appeal):
                    mime = content_type or "application/octet-stream"
                    with path.open("rb") as file_handle:
                        doc_response = await client.post(
                            f"{base_url}/sendDocument",
                            data={"chat_id": chat_id},
                            files={"document": (filename, file_handle, mime)},
                        )
                    if doc_response.is_error:
                        logger.error(
                            "Telegram sendDocument error for user %s file %s: %s %s",
                            user.id,
                            filename,
                            doc_response.status_code,
                            doc_response.text,
                        )
                    else:
                        files_sent += 1

            logger.info(
                "Telegram notification sent to user %s (chat_id=%s, %s files)",
                user.id,
                user.telegram_chat_id,
                files_sent,
            )
            return True
        except Exception:
            logger.exception("Failed to send Telegram to user %s (chat_id=%s)", user.id, user.telegram_chat_id)
            return False
