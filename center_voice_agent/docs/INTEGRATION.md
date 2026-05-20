# Интеграция: center_voice_agent ↔ голосовой бот

## Граница ответственности

| Компонент | Репозиторий / пакет | Задача |
|-----------|---------------------|--------|
| ASR (речь → текст) | `13_reber`, `voice_assistant` | Распознавание |
| **Агент (текст)** | **`center_voice_agent`** | Режим, сценарий, память, LLM, tools |
| TTS (текст → речь) | `13_reber`, `voice_assistant` | Озвучка |
| Установщик / UI | `voice_assistant/installer_output` | Доставка пользователю |

Агент **не** открывает микрофон и **не** синтезирует звук.

## Простой способ (рекомендуется)

```python
from center_voice_agent.integration.bridge import AgentSession

session = await AgentSession.open(
    session_id="room-1",
    child_profile_id="child-uuid",
    age_band="5-6",
    scenario_id="check_in_three",  # опционально
)
result = await session.ask(asr_text)
tts_text = session.spoken_text(result)
await session.close()
```

Синхронно (GUI): `ask_once_sync("Привет!", session_id="room-1")`.

Голосовой помощник: `voice_assistant/center_agent_bridge.py` + `USE_CENTER_AGENT=true`.

## Контракт вызова (низкий уровень)

```python
from center_voice_agent.composition.container import AppContainer
from center_voice_agent.context.short_term import ShortTermMemory
from center_voice_agent.settings import get_settings

settings = get_settings()
container = AppContainer.from_settings(settings)
coord = container.build_coordinator()
stm = ShortTermMemory(max_turns=settings.short_term_max_messages)

result = await coord.handle_user_turn(
    session_id="unique-session-id",
    child_profile_id="child-uuid",
    user_text=asr_text,
    short_term=stm,
    age_band="5-6",
)

tts_text = result.reply_spoken or result.text
await coord.gateway.aclose()
```

Перед первым ходом: `init_db`, при сценарии — `session_repository.attach_scenario(session_id, "check_in_three")`.

## CLI для отладки без голоса

```bash
python -m center_voice_agent.cli.text_turn
python -m center_voice_agent.cli.text_turn --live
```

## Переменные окружения

Скопировать из `center_voice_agent/.env.example` в процесс бота или загрузить через `pydantic-settings` из каталога `center_voice_agent/`.
