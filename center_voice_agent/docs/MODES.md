# Режимы наставника (`config/modes/`)

Режимы по умолчанию задаются **YAML-файлами** в каталоге `config/modes/`. Имя файла произвольное, важно поле **`id`** (уникально среди всех файлов).

Дополнительно можно хранить опубликованные версии в SQLite (таблица `mode_definitions`, миграция `002_mode_definitions.sql`).

## Источник данных: `MODES_SOURCE`

Переменная окружения **`MODES_SOURCE`** (см. `.env.example`):

| Значение | Поведение |
|----------|-----------|
| `files` | Только YAML из `config/modes/` (как раньше). |
| `database` | Только строки со статусом `published` в `mode_definitions`. Если в БД нет ни одной опубликованной записи, используется **fallback на файлы** (и в лог пишется `database_modes_empty_fallback_files`). |
| `hybrid` | Сначала загружаются все YAML из каталога, затем для каждого `mode_id` из БД конфиг **перезаписывается** опубликованным YAML из таблицы. |

Опционально **`MODES_CENTER_ID`**: при загрузке из БД учитываются строки с `center_id = MODES_CENTER_ID` и глобальные (`center_id IS NULL`); для одного `mode_id` приоритет у строки центра.

Синхронная выборка из БД поддерживает только URL вида `sqlite+aiosqlite:///...` (тот же файл, что и у основного приложения).

## Публикация YAML в БД

После `python -m center_voice_agent.cli.init_db` (миграции `001` и `002`):

```bash
python -m center_voice_agent.cli.modes_publish path/to/mode.yaml
python -m center_voice_agent.cli.modes_publish path/to/mode.yaml --center-id my_center
python -m center_voice_agent.cli.modes_publish path/to/mode.yaml --draft
```

Поле `id` в YAML задаёт `mode_id` в таблице (можно переопределить флагом `--mode-id`). Для `published` прежняя опубликованная строка с тем же `mode_id` и `center_id` удаляется перед вставкой новой версии.

## Поля режима

| Поле | Обязательно | Описание |
|------|-------------|----------|
| `id` | да | Идентификатор `snake_case`, латиница: `dialog`, `lesson`, `play`. |
| `display_name` | да | Человекочитаемое имя для ответов и логов. |
| `system_prompt` | условно | Текст системного промпта, если нет `system_prompt_path`. |
| `system_prompt_path` | нет | Путь: **абсолютный**; или `./...` — сначала от каталога с YAML режима (`config/modes/`), при отсутствии файла — от корня репозитория. Перекрывает inline `system_prompt`. |
| `llm_params` | нет | `temperature`, `max_tokens` и др. для LangChain `ChatOpenAI`. |
| `tool_ids` | нет | Список инструментов: `web_search`, `memory_search`, `memory_upsert` (см. `tools/factory.py`). |
| `allowed_transitions` | нет | Список `mode_id`, куда можно перейти из этого режима. **Пустой список** = разрешены все загруженные режимы. |
| `voice_aliases` | нет | Дополнительные фразы для смены режима (см. также `config/voice/mode_commands.yaml`). |
| `description_for_admin` | нет | Подсказка методисту, в LLM не попадает. |
| `max_tool_rounds` | нет | Лимит раундов tool-calling за один ход (по умолчанию 10). |

## Переключение режима

1. **Сессия** хранит текущий `mode_id` в таблице `session_state` (см. миграцию `001_init.sql`).
2. Класс **`SessionCoordinator`** (`orchestration/coordinator.py`) перед LLM проверяет текст пользователя:
   - словарь `config/voice/mode_commands.yaml`;
   - плюс `voice_aliases` из всех режимов.
3. Если переход **не разрешён** `allowed_transitions`, режим не меняется, текст уходит в обычный `run_turn`.

## Возраст

Файл `config/age_bands/default.yaml`: `default_block` и словарь `bands` по ключу `age_band` ребёнка (например `5-6`). Шлюз добавляет блок в системное сообщение, если передан параметр `age_band` в `run_turn` / `handle_user_turn`.

## Режим по умолчанию

Переменная окружения **`DEFAULT_MODE_ID`** (см. `.env.example`), используется при первом создании строки сессии.

## Новый инструмент

1. Реализовать логику в `tools/` и зарегистрировать в `tools/factory.py`.
2. Добавить `tool_id` в нужные YAML режимов.

## Перезагрузка конфигов

`ModeRegistry.reload_all()` перечитывает все `*.yaml` и валидирует `allowed_transitions`.

Из процесса без рестарта (после правки YAML на диске):

```bash
python -m center_voice_agent.cli.reload_modes
```

Печатает строку `OK: dialog, lesson, ...` и пишет в лог событие `mode_registry_loaded` (с полем `mode_files`).

## Наблюдаемость

При каждой загрузке в лог уходит поле **`mode_files`**: для каждого `*.yaml` — `name`, **`mtime_utc`** (ISO-8601, UTC), `size_bytes`. Так проще сопоставить поведение агента с версией файлов на диске.
