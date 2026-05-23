from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal, get_db
from app.models.appeal import Appeal, Attachment
from app.models.topic import Topic
from app.schemas.appeal import AppealCreate
from app.schemas.topic import TopicResponse
from app.services.notifications import notify_new_appeal
from app.services.uploads import save_upload

router = APIRouter()


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
    text: Annotated[str, Form(min_length=1, max_length=10000)],
    db: Annotated[AsyncSession, Depends(get_db)],
    files: list[UploadFile] = File(default=[]),
) -> dict:
    """Anonymous appeal submission with optional attachments."""
    payload = AppealCreate(topic_id=topic_id, text=text)

    topic_result = await db.execute(
        select(Topic).where(Topic.id == payload.topic_id, Topic.is_active.is_(True))
    )
    if topic_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Topic not found or inactive")

    appeal = Appeal(topic_id=payload.topic_id, text=payload.text)
    db.add(appeal)
    await db.flush()

    for upload in files:
        if not upload.filename:
            continue
        original, stored, content_type, size = await save_upload(upload)
        db.add(
            Attachment(
                appeal_id=appeal.id,
                original_filename=original,
                stored_filename=stored,
                content_type=content_type,
                size_bytes=size,
            )
        )

    await db.flush()
    appeal_id = appeal.id

    async def _notify() -> None:
        async with AsyncSessionLocal() as session:
            await notify_new_appeal(session, appeal_id)
            await session.commit()

    background_tasks.add_task(_notify)

    return {"id": appeal_id, "message": "Обращение принято"}
