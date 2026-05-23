# Платформа обратной связи — Backend (Python)

Анонимная подача обращений сотрудниками и панель обработки для авторизованных пользователей. При новом обращении все активные пользователи панели получают уведомления по email и/или Telegram.

## Стек

- **FastAPI** — REST API
- **SQLAlchemy 2** (async) — БД
- **JWT** — авторизация панели
- **aiosmtplib** / **httpx** — уведомления

## Быстрый старт

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env          # отредактируйте SECRET_KEY и SMTP/Telegram
python scripts/seed.py
uvicorn app.main:app --reload
```

Документация API: http://localhost:8000/docs

Учётная запись после seed: `admin@example.com` / `changeme123`

## Роли

| Роль | Возможности |
|------|-------------|
| `admin` | Управление пользователями, темами, обращениями |
| `operator` | Темы, входящие обращения (без управления пользователями) |

Самостоятельная регистрация не предусмотрена — пользователей создаёт администратор.

## API

### Публичные (без авторизации)

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/public/topics` | Список активных тем |
| POST | `/api/public/appeals` | Отправка обращения (`multipart/form-data`: `topic_id`, `text`, `files[]`) |

### Панель (Bearer token)

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/api/admin/auth/login` | Вход |
| GET/POST/PATCH/DELETE | `/api/admin/users` | Пользователи (только admin) |
| GET/POST/PATCH/DELETE | `/api/admin/topics` | Темы |
| GET | `/api/admin/appeals` | Список обращений |
| GET | `/api/admin/appeals/{id}` | Детали |
| PATCH | `/api/admin/appeals/{id}/status` | Смена статуса |
| GET | `/api/admin/appeals/{id}/attachments/{aid}/download` | Скачать вложение |

### Пример: отправка обращения

```bash
curl -X POST http://localhost:8000/api/public/appeals \
  -F "topic_id=1" \
  -F "text=Текст обращения" \
  -F "files=@document.pdf"
```

### Пример: вход в панель

```bash
curl -X POST http://localhost:8000/api/admin/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"admin@example.com\",\"password\":\"changeme123\"}"
```

## Уведомления

При создании обращения в фоне вызывается `notify_new_appeal`: всем **активным** пользователям панели отправляются сообщения по включённым каналам:

- **Email** — если `notify_email=true` и настроен SMTP (`.env`)
- **Telegram** — если `notify_telegram=true`, указан `telegram_chat_id` и `TELEGRAM_BOT_TOKEN`

Настройки каналов задаются при создании/редактировании пользователя администратором.

## Переменные окружения

См. `.env.example`. Для production обязательно смените `SECRET_KEY` и используйте PostgreSQL:

```
DATABASE_URL=postgresql+asyncpg://user:pass@host/db
```

(добавьте `asyncpg` в зависимости при переходе на PostgreSQL)

## Структура проекта

```
app/
  api/           # public + admin роуты
  auth/          # JWT, зависимости
  models/        # User, Topic, Appeal, Attachment
  schemas/       # Pydantic
  services/      # загрузка файлов, уведомления
  main.py
scripts/seed.py
```
