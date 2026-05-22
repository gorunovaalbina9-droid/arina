# Сценарии (граф узлов)

Сценарии задаются YAML в каталоге **`config/scenarios/`** (путь задаётся в настройках как `scenarios_dir`). Имя файла произвольно; идентификатор сценария — поле **`id`** в YAML (уникален среди всех `*.yaml` в каталоге).

## Поля графа

| Поле | Описание |
|------|----------|
| `id` | Строка, по ней сессия ссылается через `session_state.scenario_id`. |
| `version` | Целое, для учёта версий (логика/миграции позже). |
| `entry` | id стартового узла. |
| `default_on_interrupt` | Политика сброса по умолчанию (см. ниже), если у узла нет своей. |
| `nodes` | Словарь `node_id` → узел. |

### Узел

| Поле | Описание |
|------|----------|
| `title` | Человекочитаемое имя этапа. |
| `prompt_to_model` | Текст, добавляемый в системный промпт шлюза как «текущий этап». |
| `transitions` | Список рёбер `{ when, next }`. |
| `on_interrupt` | Опционально: переопределение политики для фраз сброса (см. ниже). |

### Переходы (`when`)

См. [SCENARIOS_WHEN_SPEC.md](SCENARIOS_WHEN_SPEC.md).

- **`turn_complete`** — после ответа ассистента за один ход.
- **`user_spoke`** — алиас к `turn_complete`.
- **`always`** — при событии turn_complete.
- **`keyword:слово1,слово2`** — по тексту **ребёнка до LLM** (подстрока).

Порядок в списке важен: срабатывает **первое** совпадение.

**Стенд hybrid:** [SCENARIOS_HYBRID_STAND.md](SCENARIOS_HYBRID_STAND.md).

### Сброс сценария (`on_interrupt`)

Объект:

```yaml
on_interrupt:
  action: stay           # stay | reset_to_entry | goto
  target: wrap_up        # только для action: goto
```

Фразы сброса задаются в **`config/voice/scenario_commands.yaml`** (список `reset_phrases`). При совпадении координатор вызывает политику **текущего узла** или `default_on_interrupt` графа, затем один LLM-ход **без** автоматического продвижения по `turn_complete`.

## Сессия и БД

В таблице **`session_state`** уже есть поля `scenario_id` и `scenario_node_id`. Метод репозитория **`attach_scenario(session_id, scenario_id, node_id=None)`** включает сценарий для сессии; `NULL` у узла означает при следующей загрузке старт с `entry`.

После каждого хода координатор обновляет указатель на текущий узел.

## Пример

Файл **`config/scenarios/example_linear.yaml`** — линейный сценарий на три узла с политикой `on_interrupt` на среднем узле.

## Загрузка по id

`load_scenario_by_id(scenarios_dir, scenario_id)` сканирует `*.yaml` и ищет совпадение по полю `id`.

## Публикация в SQLite (`scenario_publish`)

Миграция **`004_scenario_publish.sql`**: таблица **`scenario_publish`** (поля `scenario_id`, `center_id`, `status`, `version`, `config_yaml`, опционально `subject`, `age_band`). Семантика как у **`mode_definitions`**: опубликованная строка с тем же `scenario_id` и `center_id` заменяется при новой публикации.

Переменные окружения:

- **`SCENARIOS_SOURCE`**: `files` | `database` | `hybrid` (файлы + поверх YAML из БД по `id` графа).
- **`SCENARIOS_CENTER_ID`**: приоритет строк центра над глобальными (`center_id IS NULL`).

CLI после `init_db`:

```bash
python -m center_voice_agent.cli.scenarios_publish path/to/scenario.yaml
python -m center_voice_agent.cli.scenarios_publish path/to/scenario.yaml --center-id my_center --draft
```

Загрузка в рантайме: **`load_scenario_graph_unified(...)`** в `scenarios/loader.py` (используется в **`SessionCoordinator`**).

Таблица **`scenario_definitions`** из миграции `001_init.sql` (поле `graph_yaml_path`) **не используется** текущим кодом загрузки; рабочий контур — файлы и/или **`scenario_publish`**.

## LangGraph в шлюзе

Цикл **LLM ↔ tools** выполняется через **LangGraph** (`agent/turn_langgraph.py`): узлы **`agent`** и **`tools`**, условный переход по наличию `tool_calls` и лимиту **`max_tool_rounds`**.

Отключить граф и вернуться к прежнему циклу в коде:

```bash
USE_LANGGRAPH=false
```

Перемещение по узлам сценария после ответа по-прежнему в **`AgentGateway.run_turn`** (событие `turn_complete`), не внутри графа LangGraph.
