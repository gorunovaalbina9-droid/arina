# Стенд SCENARIOS_SOURCE=hybrid (6.5)

```powershell
cd center_voice_agent
.\.venv\Scripts\activate
# .env: SCENARIOS_SOURCE=hybrid
python -m center_voice_agent.cli.init_db
python -m center_voice_agent.cli.scenarios_publish config\scenarios\check_in_three.yaml
python -m center_voice_agent.cli.reload_scenarios
```

Проверка overlay: `pytest tests/test_hybrid_sources.py::test_scenarios_hybrid_overlay -q`

Сессия:

```python
await repo.attach_scenario(session_id, "check_in_three")
```

Демо: `python -m center_voice_agent.cli.demo_turn --scenario check_in_three`

Чеклист: [SCENARIOS_HYBRID_CHECKLIST.md](SCENARIOS_HYBRID_CHECKLIST.md). Условия when: [SCENARIOS_WHEN_SPEC.md](SCENARIOS_WHEN_SPEC.md).
