from datetime import datetime

from pydantic import BaseModel, Field


class TopicCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    is_active: bool = True
    sort_order: int = 0


class TopicUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    is_active: bool | None = None
    sort_order: int | None = None


class TopicResponse(BaseModel):
    id: int
    name: str
    description: str | None
    is_active: bool
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}
