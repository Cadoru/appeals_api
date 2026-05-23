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

**Ограничения:** текст до **5000** символов, каждый файл до **10 МБ** (`MAX_APPEAL_TEXT_LENGTH`, `MAX_UPLOAD_SIZE_MB` в `.env`). При превышении — ответ `400` / `413` с понятным сообщением на русском.

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

Вложения обращения прикрепляются к письму и отправляются в Telegram отдельными файлами (`sendDocument`).

Ссылка на обращение в портале формируется из `PORTAL_URL` в `.env` (например `https://portal.company.com/appeals/123`).

Настройки каналов задаются при создании/редактировании пользователя администратором.

### Email: если видите «SMTP not configured»

Приложение читает только файл **`.env`**, не `.env.example`. Нужны как минимум:

```
SMTP_HOST=smtp.gmail.com
SMTP_USER=your@gmail.com
SMTP_PASSWORD="app-password-with-spaces"
SMTP_FROM=your@gmail.com
```

Для Gmail `SMTP_FROM` должен совпадать с `SMTP_USER` (или быть настроенным алиасом). Используйте **пароль приложения** (App Password), не обычный пароль аккаунта: https://myaccount.google.com/apppasswords (нужна двухфакторная аутентификация). Пароль с пробелами — в кавычках в `.env`. После изменений **полностью перезапустите** uvicorn.

Ошибка `535 Username and Password not accepted` — неверный или устаревший App Password; создайте новый и обновите `SMTP_PASSWORD` в `.env`.

Запускайте сервер из каталога проекта с локальным venv: `.venv\Scripts\activate` → `uvicorn app.main:app --reload` (не venv из другого проекта).

### Telegram: если уведомления не приходят

1. Создайте файл **`.env`** в корне проекта (`copy .env.example .env`) — приложение **не читает** `.env.example`.
2. Укажите `TELEGRAM_BOT_TOKEN=...` в `.env` и **перезапустите** uvicorn.
3. У пользователя в панели: `notify_telegram=true` и `telegram_chat_id` (ваш chat id).
4. Напишите боту **`/start`** в Telegram — без этого бот не может писать вам первым.
5. В логах при ошибке будет ответ Telegram API; при проблемах с прокси в системе запросы к API идут напрямую (`trust_env=false`).

## Переменные окружения

Скопируйте `.env.example` в `.env` и заполните значения. См. также `.env.example`.

| Переменная | Назначение |
|------------|------------|
| `PORTAL_URL` | Адрес веб-портала (фронтенд) для ссылок в уведомлениях |
| `PUBLIC_BASE_URL` | Устаревший алиас для `PORTAL_URL` (поддерживается) |
| `TELEGRAM_BOT_TOKEN` | Токен бота |
| `SMTP_*` | Параметры почты | Для production обязательно смените `SECRET_KEY` и используйте PostgreSQL:

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
