from pathlib import Path

from app.config import get_settings
from app.models.appeal import Appeal, Attachment


def appeal_portal_url(appeal_id: int) -> str:
    """Ссылка на обращение в веб-портале (фронтенд)."""
    base = get_settings().portal_url.rstrip("/")
    return f"{base}/appeals/{appeal_id}"


def collect_attachment_files(appeal: Appeal) -> list[tuple[Path, str, str | None]]:
    """Пути к файлам вложений: (path, original_filename, content_type)."""
    upload_dir = Path(get_settings().upload_dir)
    files: list[tuple[Path, str, str | None]] = []
    for attachment in appeal.attachments:
        path = upload_dir / attachment.stored_filename
        if path.is_file():
            files.append((path, attachment.original_filename, attachment.content_type))
    return files


def attachments_summary(appeal: Appeal) -> str:
    count = len(appeal.attachments)
    if count == 0:
        return ""
    names = ", ".join(a.original_filename for a in appeal.attachments[:5])
    suffix = f" и ещё {count - 5}" if count > 5 else ""
    return f"\nВложений: {count} ({names}{suffix})"
