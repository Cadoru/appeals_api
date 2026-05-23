import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AppealStatus(str, enum.Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"


class Appeal(Base):
    __tablename__ = "appeals"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"), index=True)
    text: Mapped[str] = mapped_column(Text)
    status: Mapped[AppealStatus] = mapped_column(Enum(AppealStatus), default=AppealStatus.NEW, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    topic: Mapped["Topic"] = relationship(back_populates="appeals")  # noqa: F821
    attachments: Mapped[list["Attachment"]] = relationship(
        back_populates="appeal", cascade="all, delete-orphan"
    )


class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    appeal_id: Mapped[int] = mapped_column(ForeignKey("appeals.id", ondelete="CASCADE"), index=True)
    original_filename: Mapped[str] = mapped_column(String(512))
    stored_filename: Mapped[str] = mapped_column(String(512), unique=True)
    content_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    size_bytes: Mapped[int] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    appeal: Mapped[Appeal] = relationship(back_populates="attachments")
