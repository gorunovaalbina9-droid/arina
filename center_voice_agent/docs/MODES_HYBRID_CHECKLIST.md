# Чеклист hybrid (5.2.4)

- [x] `MODES_SOURCE=hybrid` в `.env` (стенд: env при reload)
- [x] `init_db` OK
- [x] `modes_publish` → `status=published`
- [x] `reload_modes` → `OK: calm, dialog, lesson, play`
- [x] `pytest tests/test_hybrid_sources.py::test_modes_hybrid_overlay` green
- [ ] `demo_turn` — `modes_resolve` в логах (при необходимости)
- [ ] Смена режима фразой из `config/voice/mode_commands.yaml`
- [ ] `allowed_transitions` — запрещённый переход не меняет mode (см. coordinator)
- [ ] Документирован откат (MODES_HYBRID_STAND.md)
