from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_panel_user
from app.database import get_db
from app.models.topic import Topic
from app.models.user import User
from app.schemas.topic import TopicCreate, TopicResponse, TopicUpdate

router = APIRouter()


@router.get("", response_model=list[TopicResponse])
async def list_topics(
    _: Annotated[User, Depends(require_panel_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[Topic]:
    result = await db.execute(select(Topic).order_by(Topic.sort_order, Topic.name))
    return list(result.scalars().all())


@router.post("", response_model=TopicResponse, status_code=status.HTTP_201_CREATED)
async def create_topic(
    payload: TopicCreate,
    _: Annotated[User, Depends(require_panel_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Topic:
    existing = await db.execute(select(Topic).where(Topic.name == payload.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Topic name already exists")

    topic = Topic(**payload.model_dump())
    db.add(topic)
    await db.flush()
    await db.refresh(topic)
    return topic


@router.patch("/{topic_id}", response_model=TopicResponse)
async def update_topic(
    topic_id: int,
    payload: TopicUpdate,
    _: Annotated[User, Depends(require_panel_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Topic:
    result = await db.execute(select(Topic).where(Topic.id == topic_id))
    topic = result.scalar_one_or_none()
    if topic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(topic, key, value)

    await db.flush()
    await db.refresh(topic)
    return topic


@router.delete("/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_topic(
    topic_id: int,
    _: Annotated[User, Depends(require_panel_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    result = await db.execute(select(Topic).where(Topic.id == topic_id))
    topic = result.scalar_one_or_none()
    if topic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")

    await db.delete(topic)
