import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import hash_password, require_admin
from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.repositories.user_repository import UserRepository

router = APIRouter()


@router.get("", response_model=list[UserResponse])
async def list_users(
    _: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[User]:
    repo = UserRepository(db)
    users = await repo.list()
    return users


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    _: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
)-> User:
    repo = UserRepository(db)
    user = await repo.get_by_email(payload.email)
    
    if user:
         raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        notify_email=payload.notify_email,
        notify_telegram=payload.notify_telegram,
        telegram_chat_id=payload.telegram_chat_id,
    )
    await repo.create(user=user)
    logging.info(f"User created: {user.email} with role {user.role}")
    return user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    current: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    data = payload.model_dump(exclude_unset=True)
    
    # Handle email change - check if new email is unique
    if "email" in data and data["email"] != user.email:
        existing_user = await repo.get_by_email(data["email"])
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email {data['email']} is already in use"
            )
        logging.info(f"User {user.id} email changed from {user.email} to {data['email']}")
    
    # Handle password change
    if "password" in data:
        data["hashed_password"] = hash_password(data.pop("password"))
        logging.info(f"User {user.id} ({user.email}) password changed")
        
    # Prevent operator from changing role
    if "role" in data and current.role == UserRole.OPERATOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can change user role"
        )
    
    # Prevent changing admin role (optional security measure)
    if "role" in data and data["role"] == UserRole.ADMIN and user.role != UserRole.ADMIN:
        if current.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin can grant admin role"
            )
        logging.warning(f"User {user.id} ({user.email}) promoted to admin by {current.email}")

    for key, value in data.items(): setattr(user, key, value)

    await repo.update(user)
    
    logging.info(f"User {user.id} ({user.email}) updated")
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    if user_id == current.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete yourself")

    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if user is None:  raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    await repo.delete(user)
    logging.warning(f"User deleted: {user.email}")
