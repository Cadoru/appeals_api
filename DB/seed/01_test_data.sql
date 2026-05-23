-- Тестовые данные (выполнять после init/01_schema.sql)
PRAGMA foreign_keys = ON;

-- Каналы уведомлений
INSERT INTO notification_channels (code, name) VALUES
    ('email',    'Электронная почта'),
    ('telegram', 'Telegram');

-- Пользователи панели
-- Пароль для всех тестовых учёток: password
-- bcrypt hash (cost 10) для строки "password"
INSERT INTO users (login, email, password_hash, full_name, role) VALUES
    (
        'admin',
        'admin@company.local',
        '$2b$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy',
        'Администратор Системы',
        'administrator'
    ),
    (
        'ivanova',
        'ivanova@company.local',
        '$2b$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy',
        'Иванова Мария',
        'operator'
    ),
    (
        'petrov',
        'petrov@company.local',
        '$2b$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy',
        'Петров Алексей',
        'operator'
    );

-- Темы обращений
INSERT INTO appeal_topics (name, description, sort_order) VALUES
    ('Неудобный вопрос руководству', 'Вопросы, которые сложно задать лично', 10),
    ('Проблема в процессе',         'Сбои, задержки, неэффективные процедуры', 20),
    ('Замечание по работе команды', 'Конструктивная обратная связь',           30),
    ('Благодарность коллеге',       'Публичная благодарность без указания имени отправителя', 40),
    ('Другое',                      'Прочие обращения',                        50);

-- Настройки уведомлений (все активные пользователи панели)
INSERT INTO user_notification_settings (user_id, channel_id, destination) VALUES
    (1, 1, 'admin@company.local'),
    (1, 2, '@admin_feedback_bot'),
    (2, 1, 'ivanova@company.local'),
    (2, 2, '@ivanova_hr_bot'),
    (3, 1, 'petrov@company.local');

-- Примеры анонимных обращений
INSERT INTO appeals (topic_id, body_text, status, created_at) VALUES
    (
        1,
        'Хотелось бы уточнить политику удалённой работы на следующий квартал. Сейчас информация расходится в разных каналах.',
        'new',
        datetime('now', '-2 days')
    ),
    (
        2,
        'Согласование заявок в системе занимает до двух недель. Это блокирует запуск проектов.',
        'in_progress',
        datetime('now', '-1 days')
    ),
    (
        4,
        'Спасибо коллегам из отдела поддержки за быструю помощь в пятницу вечером!',
        'resolved',
        datetime('now', '-5 hours')
    );

-- Вложения (пути — условные, для интеграции с файловым хранилищем API)
INSERT INTO appeal_attachments (appeal_id, file_name, storage_path, mime_type, file_size_bytes) VALUES
    (2, 'screenshot_delay.png', 'uploads/2026/05/appeal_2/screenshot_delay.png', 'image/png', 245760),
    (2, 'process_map.pdf',      'uploads/2026/05/appeal_2/process_map.pdf',      'application/pdf', 1048576);

-- Уведомления о новых обращениях (имитация очереди отправки)
INSERT INTO notifications (appeal_id, user_id, channel_id, status, sent_at) VALUES
    (1, 1, 1, 'sent', datetime('now', '-2 days', '+5 minutes')),
    (1, 1, 2, 'sent', datetime('now', '-2 days', '+5 minutes')),
    (1, 2, 1, 'sent', datetime('now', '-2 days', '+6 minutes')),
    (1, 3, 1, 'sent', datetime('now', '-2 days', '+6 minutes')),
    (2, 1, 1, 'sent', datetime('now', '-1 days', '+3 minutes')),
    (2, 2, 1, 'pending', NULL),
    (3, 1, 1, 'sent', datetime('now', '-5 hours', '+2 minutes'));
