# PR: `center-voice-agent` → `master`

**Title:** `feat: center_voice_agent — память, режимы, сценарии, модерация, пилот`

## Summary

- **Агент:** LangGraph tool-loop, `SessionCoordinator`, hybrid режимы/сценарии из YAML+SQLite.
- **Память:** долгая + краткая (`session_messages`, `SHORT_TERM_SOURCE=db`), отчёт родителю CLI.
- **Безопасность:** модерация in/out, rate limit, audit tools, LIKE escape.
- **Пилот:** `docs/pilot/*`, `purge_child`, bat-скрипты.
- **Интеграция:** `voice_assistant/center_agent_bridge.py`, offline fake LLM.

## What's NOT in this PR

- Live LLM / дообученная модель (403 region — отдельно после merge).
- MCP, RAG, PostgreSQL, полный ASR/TTS E2E.

## Test plan

```powershell
cd center_voice_agent
.\.venv\Scripts\activate
pip install -e ".[dev]"
python -m center_voice_agent.cli.init_db
python -m center_voice_agent.cli.block2_offline
python -m pytest tests/ -q
python -m center_voice_agent.cli.demo_turn
python -m center_voice_agent.cli.demo_turn --scenario check_in_three
```

```powershell
cd voice_assistant
$env:USE_CENTER_AGENT="true"
..\center_voice_agent\.venv\Scripts\python.exe voice_loop_text.py
```

## After merge

1. `init_db` на стенде (миграция `005_session_messages.sql`).
2. Заполнить `docs/pilot/PASSPORT.md`, `ONCALL.md`.
3. Live: `LLM_BASE_URL` + `live_acceptance` когда API готов.

## Commits ahead of master

См. `git log master..center-voice-agent` — блоки 4, 6, интеграция voice, и др.
