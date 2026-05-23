-- SQLite schema: сервис приёма анонимных обращений
-- PRAGMA для внешних ключей обязателен в SQLite
PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------------
-- Справочник каналов уведомлений (почта, Telegram и т.д.)
-- ---------------------------------------------------------------------------
CREATE TABLE notification_channels (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    code            TEXT    NOT NULL UNIQUE,
    name            TEXT    NOT NULL,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------------------
-- Пользователи панели обработки (без самостоятельной регистрации)
-- role: administrator — управление пользователями и темами
--       operator       — просмотр обращений и получение уведомлений
-- ---------------------------------------------------------------------------
CREATE TABLE users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    login           TEXT    NOT NULL UNIQUE,
    email           TEXT    NOT NULL UNIQUE,
    password_hash   TEXT    NOT NULL,
    full_name       TEXT,
    role            TEXT    NOT NULL CHECK (role IN ('administrator', 'operator')),
    is_active       INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_users_role ON users (role);
CREATE INDEX idx_users_is_active ON users (is_active);

-- ---------------------------------------------------------------------------
-- Темы обращений (редактируются в панели)
-- ---------------------------------------------------------------------------
CREATE TABLE appeal_topics (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL UNIQUE,
    description     TEXT,
    sort_order      INTEGER NOT NULL DEFAULT 0,
    is_active       INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_appeal_topics_is_active_sort
    ON appeal_topics (is_active, sort_order);

-- ---------------------------------------------------------------------------
-- Анонимные обращения (отправитель не хранится)
-- ---------------------------------------------------------------------------
CREATE TABLE appeals (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id        INTEGER NOT NULL,
    body_text       TEXT    NOT NULL,
    status          TEXT    NOT NULL DEFAULT 'new'
                            CHECK (status IN ('new', 'in_progress', 'resolved', 'closed')),
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (topic_id) REFERENCES appeal_topics (id)
);

CREATE INDEX idx_appeals_topic_id ON appeals (topic_id);
CREATE INDEX idx_appeals_status ON appeals (status);
CREATE INDEX idx_appeals_created_at ON appeals (created_at DESC);
CREATE INDEX idx_appeals_status_created_at ON appeals (status, created_at DESC);

-- ---------------------------------------------------------------------------
-- Вложения к обращениям (файлы хранятся вне БД; путь — для сервиса API)
-- ---------------------------------------------------------------------------
CREATE TABLE appeal_attachments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    appeal_id       INTEGER NOT NULL,
    file_name       TEXT    NOT NULL,
    storage_path    TEXT    NOT NULL,
    mime_type       TEXT,
    file_size_bytes INTEGER,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (appeal_id) REFERENCES appeals (id) ON DELETE CASCADE
);

CREATE INDEX idx_appeal_attachments_appeal_id ON appeal_attachments (appeal_id);

-- ---------------------------------------------------------------------------
-- Настройки уведомлений пользователей панели по каналам
-- ---------------------------------------------------------------------------
CREATE TABLE user_notification_settings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    channel_id      INTEGER NOT NULL,
    destination     TEXT    NOT NULL,
    is_enabled      INTEGER NOT NULL DEFAULT 1 CHECK (is_enabled IN (0, 1)),
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (channel_id) REFERENCES notification_channels (id),
    UNIQUE (user_id, channel_id)
);

CREATE INDEX idx_user_notification_settings_user_id
    ON user_notification_settings (user_id);
CREATE INDEX idx_user_notification_settings_enabled
    ON user_notification_settings (is_enabled);

-- ---------------------------------------------------------------------------
-- Журнал уведомлений о новых обращениях
-- ---------------------------------------------------------------------------
CREATE TABLE notifications (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    appeal_id       INTEGER NOT NULL,
    user_id         INTEGER NOT NULL,
    channel_id      INTEGER NOT NULL,
    status          TEXT    NOT NULL DEFAULT 'pending'
                            CHECK (status IN ('pending', 'sent', 'failed')),
    error_message   TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    sent_at         TEXT,
    FOREIGN KEY (appeal_id) REFERENCES appeals (id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (channel_id) REFERENCES notification_channels (id)
);

CREATE INDEX idx_notifications_appeal_id ON notifications (appeal_id);
CREATE INDEX idx_notifications_user_id ON notifications (user_id);
CREATE INDEX idx_notifications_status ON notifications (status);
CREATE INDEX idx_notifications_pending ON notifications (status, created_at)
    WHERE status = 'pending';
