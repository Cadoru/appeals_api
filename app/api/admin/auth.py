from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import create_access_token, verify_password
from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: Annotated[AsyncSession, Depends(get_db)]) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(user.email)
    return TokenResponse(access_token=token)
