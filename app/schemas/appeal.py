from datetime import datetime

from pydantic import BaseModel, Field

from app.models.appeal import AppealStatus


class AttachmentResponse(BaseModel):
    id: int
    original_filename: str
    content_type: str | None
    size_bytes: int
    download_url: str

    model_config = {"from_attributes": True}


class AppealCreate(BaseModel):
    topic_id: int
    text: str = Field(min_length=1, max_length=10000)


class AppealListItem(BaseModel):
    id: int
    topic_id: int
    topic_name: str
    text_preview: str
    status: AppealStatus
    attachments_count: int
    created_at: datetime


class AppealDetail(BaseModel):
    id: int
    topic_id: int
    topic_name: str
    text: str
    status: AppealStatus
    attachments: list[AttachmentResponse]
    created_at: datetime
    updated_at: datetime


class AppealStatusUpdate(BaseModel):
    status: AppealStatus
