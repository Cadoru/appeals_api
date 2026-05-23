from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config import get_settings


def _validation_message(err: dict) -> str:
    loc = err.get("loc", ())
    field = loc[-1] if loc else "поле"
    err_type = err.get("type", "")

    if field == "text":
        if err_type == "string_too_long":
            limit = get_settings().max_appeal_text_length
            return f"Текст обращения не должен превышать {limit} символов"
        if err_type in ("string_too_short", "missing"):
            return "Укажите текст обращения"

    if field == "topic_id" and err_type == "missing":
        return "Выберите тему обращения"

    if field == "files":
        return "Некорректный формат вложения"

    msg = err.get("msg", "Некорректные данные")
    return str(msg)


async def appeal_validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, RequestValidationError):
        raise exc

    if request.url.path.endswith("/appeals") and request.method == "POST":
        messages = [_validation_message(e) for e in exc.errors()]
        detail = messages[0] if len(messages) == 1 else messages
        return JSONResponse(status_code=422, content={"detail": detail})

    return JSONResponse(status_code=422, content={"detail": exc.errors()})
