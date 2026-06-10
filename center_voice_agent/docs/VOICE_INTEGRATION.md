# Интеграция STT/TTS (пункт 28 scope)

Распознавание и синтез речи **не входят** в `center_voice_agent`. Пакет отвечает за
логику наставника: режимы, память, модерацию, LLM, инструменты.

## Рекомендуемая схема

```
Микрофон → [voice_assistant STT] → текст
       → center_voice_agent (POST /turn или WS /ws/session)
       → reply_spoken / text
       → [voice_assistant TTS] → динамик
```

## Мост в коде

- `integration/bridge.py` — `AgentSession` для CLI и голосового GUI
- `composition/runtime.py` — один `AppContainer` на процесс (P0 для voice-сервиса)
- HTTP API — см. [API.md](API.md)

## Настройка voice_assistant

1. Запустите `center-agent-api` или встройте `AgentSession` в процесс voice-сервиса.
2. Передавайте стабильные `session_id` и `child_profile_id` на каждый ход.
3. Для офлайн-пилота: `offline_llm=true` в WS или `StaticChatModel` в bridge.

## Что не делаем здесь

- Выбор модели STT/TTS, VAD, wake word
- GUI родителя и веб-кабинет (п. 29 scope)
