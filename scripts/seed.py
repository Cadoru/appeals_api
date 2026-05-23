"""Create initial admin user and sample topics."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.auth.security import hash_password
from app.database import AsyncSessionLocal, Base, engine
from app.models.topic import Topic
from app.models.user import User, UserRole

DEFAULT_ADMIN_EMAIL = "admin@example.com"
DEFAULT_ADMIN_PASSWORD = "changeme123"


async def seed() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        existing = await db.execute(select(User).where(User.email == DEFAULT_ADMIN_EMAIL))
        if existing.scalar_one_or_none() is None:
            db.add(
                User(
                    email=DEFAULT_ADMIN_EMAIL,
                    full_name="Administrator",
                    hashed_password=hash_password(DEFAULT_ADMIN_PASSWORD),
                    role=UserRole.ADMIN,
                    notify_email=True,
                )
            )
            print(f"Created admin: {DEFAULT_ADMIN_EMAIL} / {DEFAULT_ADMIN_PASSWORD}")

        topics = [
            ("Неудобный вопрос", "Вопросы, которые сложно задать лично", 1),
            ("Боль / проблема", "Рабочие трудности и препятствия", 2),
            ("Замечание", "Предложения по улучшению процессов", 3),
            ("Благодарность коллеге", "Анонимная благодарность", 4),
        ]
        for name, description, sort_order in topics:
            found = await db.execute(select(Topic).where(Topic.name == name))
            if found.scalar_one_or_none() is None:
                db.add(Topic(name=name, description=description, sort_order=sort_order))

        await db.commit()
        print("Seed completed.")


if __name__ == "__main__":
    asyncio.run(seed())
