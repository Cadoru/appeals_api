import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import AsyncSessionLocal, get_db
from app.models.appeal import Appeal, Attachment
from app.models.topic import Topic
from app.schemas.appeal import AppealCreate
from app.schemas.topic import TopicResponse
from app.services.notifications import notify_new_appeal
from app.services.uploads import read_upload, save_upload_bytes

logger = logging.getLogger(__name__)
router = APIRouter()


def _validate_appeal_text(text: str) -> str:
    settings = get_settings()
    if len(text) > settings.max_appeal_text_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Текст обращения не должен превышать "
                f"{settings.max_appeal_text_length} символов (сейчас {len(text)})"
            ),
        )
    if not text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Текст обращения не может быть пустым",
        )
    return text


async def _read_all_uploads(files: list[UploadFile]) -> list[tuple[str, bytes, str | None]]:
    """Проверить все вложения до создания обращения в БД."""
    prepared: list[tuple[str, bytes, str | None]] = []
    for upload in files:
        if not upload.filename:
            continue
        try:
            prepared.append(await read_upload(upload))
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("Failed to read upload %s", upload.filename)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Не удалось обработать файл «{upload.filename}»",
            ) from exc
    return prepared


@router.get("/topics", response_model=list[TopicResponse])
async def list_active_topics(db: Annotated[AsyncSession, Depends(get_db)]) -> list[Topic]:
    result = await db.execute(
        select(Topic).where(Topic.is_active.is_(True)).order_by(Topic.sort_order, Topic.name)
    )
    return list(result.scalars().all())


@router.post("/appeals", status_code=status.HTTP_201_CREATED)
async def submit_appeal(
    background_tasks: BackgroundTasks,
    topic_id: Annotated[int, Form()],
    text: Annotated[str, Form(min_length=1)],
    db: Annotated[AsyncSession, Depends(get_db)],
    files: list[UploadFile] = File(default=()),
) -> dict:
    """Anonymous appeal submission with optional attachments."""
    text = _validate_appeal_text(text)
    payload = AppealCreate(topic_id=topic_id, text=text)

    try:
        prepared_files = await _read_all_uploads(files)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error while validating uploads")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при проверке вложений",
        ) from exc

    topic_result = await db.execute(
        select(Topic).where(Topic.id == payload.topic_id, Topic.is_active.is_(True))
    )
    if topic_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Тема не найдена или недоступна",
        )

    appeal = Appeal(topic_id=payload.topic_id, text=payload.text)
    db.add(appeal)

    try:
        await db.flush()

        for filename, content, content_type in prepared_files:
            original, stored, saved_type, size = await save_upload_bytes(
                filename, content, content_type
            )
            db.add(
                Attachment(
                    appeal_id=appeal.id,
                    original_filename=original,
                    stored_filename=stored,
                    content_type=saved_type,
                    size_bytes=size,
                )
            )

        await db.flush()
        appeal_id = appeal.id
    except HTTPException:
        await db.rollback()
        raise
    except Exception as exc:
        await db.rollback()
        logger.exception("Failed to save appeal or attachments")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось сохранить обращение",
        ) from exc

    async def _notify() -> None:
        try:
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    await notify_new_appeal(session, appeal_id)
        except Exception:
            logger.exception("Notification failed for appeal %s", appeal_id)

    background_tasks.add_task(_notify)
    await db.commit()

    return {"id": appeal_id, "message": "Обращение принято"}
