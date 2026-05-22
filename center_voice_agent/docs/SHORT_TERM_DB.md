# Краткая память в БД (`SHORT_TERM_SOURCE=db`)

По умолчанию реплики хранятся **в RAM** (`SHORT_TERM_SOURCE=memory`). После рестарта процесса контекст теряется.

## Включение

```env
SHORT_TERM_SOURCE=db
SHORT_TERM_MAX_MESSAGES=15
```

Таблица `session_messages` (миграция `005_session_messages.sql`). Запись — в конце каждого хода в `SessionCoordinator`; загрузка — при `AgentSession.open()` / `build_short_term_memory()`.

## Когда нужно

- Один `session_id` на несколько запусков CLI / перезапуск сервера между репликами.
- Пилот с долгими сессиями.

## Когда не нужно

- `demo_turn` / одноразовые тесты с новым `session_id` каждый раз.
- Несколько воркеров без общей БД (нужен Redis — вне scope).

## Проверка

```bash
pytest tests/test_session_messages_db.py -q
```
