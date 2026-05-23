from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.OPERATOR
    notify_email: bool = True
    notify_telegram: bool = False
    telegram_chat_id: str | None = None


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    role: UserRole | None = None
    is_active: bool | None = None
    notify_email: bool | None = None
    notify_telegram: bool | None = None
    telegram_chat_id: str | None = None


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    notify_email: bool
    notify_telegram: bool
    telegram_chat_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
