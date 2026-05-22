# Чеклист пилота с детьми

**Организация (блок 12):** [pilot/README.md](pilot/README.md) — паспорт, юрист, педагог, on-call, откат, ОС.

Перед первым реальным занятием отметьте пункты.

## Техника

- [ ] `python -m center_voice_agent.cli.setup_check` — без ошибок
- [ ] `python -m center_voice_agent.cli.live_turn` — ответ от вашей модели
- [ ] Режим по умолчанию `DEFAULT_MODE_ID` в `.env` согласован с методистом
- [ ] При сценарии: `attach_scenario` или демо с `example_linear` / `check_in_three` проверен
- [ ] Логи: `LOG_REDACT_USER_TEXT=true` (текст ребёнка не в открытом виде)

## Контент

- [ ] YAML режимов проверены методистом
- [ ] Сценарий пилота выбран и загружен
- [ ] Возрастные блоки `config/age_bands/default.yaml` актуальны

## Юридическое / этика

- [ ] Согласован список категорий долгой памяти ([MEMORY_CATEGORIES.md](MEMORY_CATEGORIES.md))
- [ ] Родители / центр проинформированы о записи диалога (если применимо)

## Голос (если не только текст)

- [ ] ASR и TTS проверены отдельно
- [ ] Текстовый чат `text_turn --live` работает
- [ ] План B: при сбое API — заранее известная фраза ребёнку

## Организация

- [ ] [PASSPORT.md](pilot/PASSPORT.md) заполнен (кто, где, дети, даты)
- [ ] [SUCCESS_CRITERIA.md](pilot/SUCCESS_CRITERIA.md) разослан команде
- [ ] [MEMORY_FOR_LAWYER.md](pilot/MEMORY_FOR_LAWYER.md) согласован с юристом
- [ ] [DATA_RETENTION.md](pilot/DATA_RETENTION.md) + бэкап `scripts/pilot_backup_db.bat`
- [ ] [PEDAGOG.md](pilot/PEDAGOG.md) + репетиция `scripts/start_pilot_text.bat`
- [ ] [ONCALL.md](pilot/ONCALL.md) — контакты заполнены
- [ ] [ROLLBACK.md](pilot/ROLLBACK.md) — стабильный коммит в паспорте
- [ ] Ответственный на занятии (взрослый)
- [ ] Контакт техподдержки / разработчика
