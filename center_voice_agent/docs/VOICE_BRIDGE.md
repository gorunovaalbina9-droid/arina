# Голос ↔ агент (без LLM в приёмке)

- Мост: `voice_assistant/center_agent_bridge.py`
- Флаг: `USE_CENTER_AGENT=true`
- Без API: по умолчанию fake LLM; для live: `CENTER_AGENT_LIVE=true`
- Вызов: `ask_center_agent(text, session_id=...)` — внутри `voice.ask_voice_sync` (долгая сессия + один container)

Проверка без микрофона:

```powershell
cd c:\Users\Альбина\глебебля2
$env:USE_CENTER_AGENT="true"
python -c "from voice_assistant.center_agent_bridge import ask_center_agent; print(ask_center_agent('Привет', session_id='bridge-test'))"
```

ASR/TTS остаются в `voice_assistant` — подключить вызов `ask_center_agent` вместо старого backend.
