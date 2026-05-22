# voice_assistant ↔ center_voice_agent

## Быстрый текстовый пилот (без микрофона)

```powershell
$env:USE_CENTER_AGENT="true"
cd voice_assistant
..\center_voice_agent\.venv\Scripts\python.exe voice_loop_text.py
```

Без API: не задавайте `CENTER_AGENT_LIVE` (используется fake LLM).

## Мост

- `center_agent_bridge.py` — `ask_center_agent()`
- Док агента: `center_voice_agent/docs/VOICE_BRIDGE.md`

## Голос (следующий шаг)

1. ASR → текст
2. `ask_center_agent(text, session_id=...)`
3. TTS ← ответ

`CENTER_AGENT_LIVE=true` — только с рабочим LLM endpoint.
