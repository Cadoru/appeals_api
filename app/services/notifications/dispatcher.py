import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.appeal import Appeal
from app.models.user import User
from app.services.notifications.email import EmailNotifier
from app.services.notifications.telegram import TelegramNotifier

logger = logging.getLogger(__name__)

_email = EmailNotifier()
_telegram = TelegramNotifier()


async def notify_new_appeal(db: AsyncSession, appeal_id: int) -> None:
    result = await db.execute(
        select(Appeal).options(selectinload(Appeal.topic)).where(Appeal.id == appeal_id)
    )
    appeal = result.scalar_one_or_none()
    if appeal is None:
        logger.error("Appeal %s not found for notification", appeal_id)
        return

    users_result = await db.execute(
        select(User).where(User.is_active.is_(True))
    )
    users = users_result.scalars().all()
    topic_name = appeal.topic.name if appeal.topic else "—"

    for user in users:
        if user.notify_email:
            await _email.send(user, appeal, topic_name)
        if user.notify_telegram or user.telegram_chat_id:
            await _telegram.send(user, appeal, topic_name)
