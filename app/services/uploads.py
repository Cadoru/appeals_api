import uuid
from pathlib import Path

import aiofiles
from fastapi import HTTPException, UploadFile, status

from app.config import get_settings


def _allowed_extensions() -> set[str]:
    settings = get_settings()
    return {ext.strip().lower() for ext in settings.allowed_extensions.split(",") if ext.strip()}


def max_upload_bytes() -> int:
    return get_settings().max_upload_size_mb * 1024 * 1024


def ensure_upload_dir() -> Path:
    path = Path(get_settings().upload_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def validate_upload(file: UploadFile) -> str:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Имя файла обязательно",
        )

    ext = Path(file.filename).suffix.lower()
    if ext not in _allowed_extensions():
        settings = get_settings()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Тип файла не разрешён. Допустимые расширения: {settings.allowed_extensions}",
        )

    return file.filename


def ensure_file_size(filename: str, size_bytes: int) -> None:
    limit = max_upload_bytes()
    if size_bytes > limit:
        settings = get_settings()
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"Файл «{filename}» превышает максимальный размер "
                f"{settings.max_upload_size_mb} МБ"
            ),
        )


async def read_upload(file: UploadFile) -> tuple[str, bytes, str | None]:
    """Проверить файл и прочитать содержимое в память."""
    filename = validate_upload(file)
    content = await file.read()
    ensure_file_size(filename, len(content))
    return filename, content, file.content_type


async def save_upload_bytes(
    filename: str,
    content: bytes,
    content_type: str | None,
) -> tuple[str, str, str | None, int]:
    ensure_file_size(filename, len(content))

    upload_dir = ensure_upload_dir()
    stored_name = f"{uuid.uuid4().hex}{Path(filename).suffix.lower()}"
    stored_path = upload_dir / stored_name

    try:
        async with aiofiles.open(stored_path, "wb") as out:
            await out.write(content)
    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось сохранить файл на сервере",
        ) from exc

    return filename, stored_name, content_type, len(content)


async def save_upload(file: UploadFile) -> tuple[str, str, str | None, int]:
    filename, content, content_type = await read_upload(file)
    return await save_upload_bytes(filename, content, content_type)
