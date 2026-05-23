from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import require_panel_user
from app.config import get_settings
from app.database import get_db
from app.models.appeal import Appeal, AppealStatus, Attachment
from app.models.topic import Topic
from app.models.user import User
from app.schemas.appeal import AppealDetail, AppealListItem, AppealStatusUpdate, AttachmentResponse

router = APIRouter()
settings = get_settings()


def _text_preview(text: str, length: int = 120) -> str:
    if len(text) <= length:
        return text
    return text[: length - 3] + "..."


@router.get("", response_model=list[AppealListItem])
async def list_appeals(
    _: Annotated[User, Depends(require_panel_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: AppealStatus | None = Query(default=None, alias="status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[AppealListItem]:
    query = (
        select(Appeal, Topic.name, func.count(Attachment.id))
        .join(Topic, Appeal.topic_id == Topic.id)
        .outerjoin(Attachment, Attachment.appeal_id == Appeal.id)
        .group_by(Appeal.id, Topic.name)
        .order_by(Appeal.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    if status_filter:
        query = query.where(Appeal.status == status_filter)

    rows = (await db.execute(query)).all()
    return [
        AppealListItem(
            id=appeal.id,
            topic_id=appeal.topic_id,
            topic_name=topic_name,
            text_preview=_text_preview(appeal.text),
            status=appeal.status,
            attachments_count=attachments_count,
            created_at=appeal.created_at,
        )
        for appeal, topic_name, attachments_count in rows
    ]


@router.get("/{appeal_id}", response_model=AppealDetail)
async def get_appeal(
    appeal_id: int,
    _: Annotated[User, Depends(require_panel_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AppealDetail:
    result = await db.execute(
        select(Appeal)
        .options(selectinload(Appeal.topic), selectinload(Appeal.attachments))
        .where(Appeal.id == appeal_id)
    )
    appeal = result.scalar_one_or_none()
    if appeal is None:
        raise HTTPException(status_code=404, detail="Appeal not found")

    attachments = [
        AttachmentResponse(
            id=a.id,
            original_filename=a.original_filename,
            content_type=a.content_type,
            size_bytes=a.size_bytes,
            download_url=f"/api/admin/appeals/{appeal_id}/attachments/{a.id}/download",
        )
        for a in appeal.attachments
    ]

    return AppealDetail(
        id=appeal.id,
        topic_id=appeal.topic_id,
        topic_name=appeal.topic.name,
        text=appeal.text,
        status=appeal.status,
        attachments=attachments,
        created_at=appeal.created_at,
        updated_at=appeal.updated_at,
    )


@router.patch("/{appeal_id}/status", response_model=AppealDetail)
async def update_appeal_status(
    appeal_id: int,
    payload: AppealStatusUpdate,
    _: Annotated[User, Depends(require_panel_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AppealDetail:
    result = await db.execute(
        select(Appeal)
        .options(selectinload(Appeal.topic), selectinload(Appeal.attachments))
        .where(Appeal.id == appeal_id)
    )
    appeal = result.scalar_one_or_none()
    if appeal is None:
        raise HTTPException(status_code=404, detail="Appeal not found")

    appeal.status = payload.status
    await db.flush()
    await db.refresh(appeal)

    attachments = [
        AttachmentResponse(
            id=a.id,
            original_filename=a.original_filename,
            content_type=a.content_type,
            size_bytes=a.size_bytes,
            download_url=f"/api/admin/appeals/{appeal_id}/attachments/{a.id}/download",
        )
        for a in appeal.attachments
    ]

    return AppealDetail(
        id=appeal.id,
        topic_id=appeal.topic_id,
        topic_name=appeal.topic.name,
        text=appeal.text,
        status=appeal.status,
        attachments=attachments,
        created_at=appeal.created_at,
        updated_at=appeal.updated_at,
    )


@router.get("/{appeal_id}/attachments/{attachment_id}/download")
async def download_attachment(
    appeal_id: int,
    attachment_id: int,
    _: Annotated[User, Depends(require_panel_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FileResponse:
    result = await db.execute(
        select(Attachment).where(
            Attachment.id == attachment_id,
            Attachment.appeal_id == appeal_id,
        )
    )
    attachment = result.scalar_one_or_none()
    if attachment is None:
        raise HTTPException(status_code=404, detail="Attachment not found")

    path = Path(settings.upload_dir) / attachment.stored_filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        path=path,
        filename=attachment.original_filename,
        media_type=attachment.content_type or "application/octet-stream",
    )
