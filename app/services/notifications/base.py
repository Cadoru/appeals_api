from abc import ABC, abstractmethod

from app.models.appeal import Appeal
from app.models.user import User


class NotificationChannel(ABC):
    @abstractmethod
    async def send(self, user: User, appeal: Appeal, topic_name: str) -> bool:
        """Send notification. Returns True on success."""
