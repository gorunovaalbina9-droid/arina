# Арина — монорепо

Репозиторий [arina](https://github.com/gorunovaalbina9-droid/arina) на GitHub.

| Папка | Назначение |
|-------|------------|
| **`center_voice_agent/`** | ИИ-наставник детского центра (LangChain) |
| `voice_assistant/` | Голосовой клиент (STT/TTS, GUI) |
| `bot.py` | Telegram-бот (отдельный контур) |

## Ветки Git

| Ветка | Назначение |
|-------|------------|
| **`center-voice-agent`** | **Рабочая ветка для агента** — клонируйте с `-b center-voice-agent` |
| `master` | Весь монорепо; push может падать из‑за файлов >100 MB в истории |

```bash
git clone -b center-voice-agent https://github.com/gorunovaalbina9-droid/arina.git
cd arina/center_voice_agent
```

Подробнее: [center_voice_agent/docs/GIT.md](center_voice_agent/docs/GIT.md).

## Голосовой помощник (пользователь)

Установщик: папка `arina-installer-repo/` (см. `README.txt` в корне при необходимости).
