# PR: center-voice-agent → master

## Summary

- Цели 0–4: каркас агента, память (в т.ч. `session_messages`), режимы hybrid, сценарии keyword/when, модерация, пилот-доки.
- Рефакторинг: `AppContainer`, `SessionCoordinator`, LangGraph tool-loop, `transitions.py`.

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

Live LLM (после merge, отдельно): `live_turn`, `live_acceptance` — нужен API вне restricted-региона.

## Scope note

`master` отстаёт на 2 коммита (блоки 6 и 4). После merge — `init_db` для миграции `005_session_messages.sql`.
