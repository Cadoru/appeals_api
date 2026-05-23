import uuid
from pathlib import Path

import aiofiles
from fastapi import HTTPException, UploadFile, status

from app.config import get_settings

settings = get_settings()


def _allowed_extensions() -> set[str]:
    return {ext.strip().lower() for ext in settings.allowed_extensions.split(",") if ext.strip()}


def ensure_upload_dir() -> Path:
    path = Path(settings.upload_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def validate_upload(file: UploadFile) -> None:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename is required")

    ext = Path(file.filename).suffix.lower()
    if ext not in _allowed_extensions():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed: {settings.allowed_extensions}",
        )


async def save_upload(file: UploadFile) -> tuple[str, str, str | None, int]:
    validate_upload(file)
    content = await file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {settings.max_upload_size_mb} MB limit",
        )

    upload_dir = ensure_upload_dir()
    stored_name = f"{uuid.uuid4().hex}{Path(file.filename).suffix.lower()}"
    stored_path = upload_dir / stored_name

    async with aiofiles.open(stored_path, "wb") as out:
        await out.write(content)

    return file.filename, stored_name, file.content_type, len(content)
