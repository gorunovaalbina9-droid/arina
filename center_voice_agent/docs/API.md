# HTTP и WebSocket API

Сервер: `center-agent-api` (FastAPI + uvicorn). OpenAPI: `/docs`.

## POST /turn

Один ход диалога (stateless на уровне HTTP — сессия в БД по `session_id`).

**Тело (JSON):**

```json
{
  "session_id": "sess-1",
  "child_profile_id": "child-1",
  "user_text": "Привет!",
  "age_band": "5-6",
  "scenario_id": null
}
```

**Ответ:**

```json
{
  "text": "...",
  "reply_spoken": "...",
  "mode_id": "dialog",
  "scenario_id": null,
  "scenario_node_id": null,
  "tool_calls": []
}
```

## WebSocket /ws/session

Потоковый диалог на одном соединении.

**Клиент → сервер:**

```json
{"type": "turn", "session_id": "s1", "child_profile_id": "c1", "user_text": "Привет"}
```

**Сервер → клиент:**

```json
{
  "type": "turn",
  "text": "...",
  "reply_spoken": "...",
  "mode_id": "dialog",
  "scenario_id": null,
  "scenario_node_id": null,
  "mode_changed": false
}
```

Дополнительно: `{"type":"ping"}` → `{"type":"pong"}`, `{"type":"close"}` → закрытие сессии.

## POST /admin/reload

Перезагрузка каталога режимов/сценариев без рестарта процесса (см. `composition/reload.py`).

## GET /health, GET /info

- `/health` — liveness
- `/info` — версия, список эндпоинтов, in/out scope

## Интеграция с голосом

STT/TTS не входят в API. Типичная схема: микрофон → STT → `POST /turn` или WS → TTS → динамик.
См. [VOICE_INTEGRATION.md](VOICE_INTEGRATION.md).
