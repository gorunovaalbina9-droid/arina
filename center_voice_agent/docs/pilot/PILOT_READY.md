# Готовность к пилоту с детьми (P0)

Чек-лист перед первым живым пилотом. Юридические процессы центра — отдельно от кода;
см. [compliance/152FZ.md](compliance/152FZ.md).

## P0 — блокеры (статус в коде)

| # | Требование | Статус | Где |
|---|------------|--------|-----|
| 1 | Усиленная модерация (regex, HTTP API, эскалация) | ✅ | `security/moderation_engine.py` |
| 2 | `web_search` выключен в детских режимах по умолчанию | ✅ | `settings.web_search_enabled=False` |
| 3 | Redact аргументов tools в логах | ✅ | `security/redact.py` |
| 4 | Один AppContainer на процесс | ✅ | `composition/runtime.py` |
| 5 | Rate limit (Redis опционально) | ✅ | `security/rate_limit_redis.py` |
| 6 | Consent hook | ✅ | `security/consent.py` |
| 7 | NLU смены режима (меньше ложных срабатываний) | ✅ | `modes/nlu.py` |
| 8 | HTTP/WS API для изолированного voice-сервиса | ✅ | `api/routes/` |

## Перед стартом пилота — ручные шаги

- [ ] Подписанные согласия родителей (152-ФЗ), регион LLM задокументирован
- [ ] `.env` без секретов в git; `WEB_SEARCH_ENABLED=false` для детских групп
- [ ] Retention логов и `session_messages` согласован с DPO центра
- [ ] Ответственный педагог на эскалации модерации
- [ ] Smoke: `pytest`, `center-agent-setup-check`, один E2E ход через `/turn`

## После P0 (не блокирует закрытый пилот)

- Векторный RAG по методичкам (сейчас keyword-stub)
- Веб-кабинет родителя
- Полноценный NLU/intent для сценариев (не только смена режима)

## Запуск API для пилота

```bash
pip install center-voice-agent[api,redis]
center-agent-init-db
center-agent-api
```

Voice-сервис шлёт текст на `POST /turn` или держит WS — см. [VOICE_INTEGRATION.md](VOICE_INTEGRATION.md).
