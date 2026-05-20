# Инструкция для вас: что сделать руками

Код наставника (**center_voice_agent**) уже написан. Ниже — только то, что **не может сделать программа без ваших ключей и решений**.

---

## Часть 1. Один раз на компьютере (30–60 минут)

### 1.1. Установите Python 3.12

1. Скачайте Python 3.12 с [python.org](https://www.python.org/downloads/).
2. При установке отметьте **«Add python.exe to PATH»**.
3. Проверка в PowerShell:

```powershell
py -3.12 --version
```

Должно показать `Python 3.12.x`.  
**Не используйте 3.14 для работы** — будут предупреждения от LangChain.

### 1.2. Откройте папку проекта

```powershell
cd "C:\Users\Альбина\глебебля2\center_voice_agent"
```

(Путь замените на свой, если репозиторий лежит в другом месте.)

### 1.3. Виртуальное окружение и библиотеки

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\activate
pip install -e ".[dev]"
```

Дождитесь окончания без красных ошибок.

### 1.4. Файл с секретами `.env`

```powershell
copy .env.example .env
notepad .env
```

**Обязательно измените три строки** (данные даст команда / хостинг модели):

| Строка | Пример | Что это |
|--------|--------|---------|
| `LLM_API_KEY` | `sk-...` | Секретный ключ API |
| `LLM_BASE_URL` | `https://api.openai.com/v1` | Адрес сервера (у дообученной модели — свой URL) |
| `LLM_MODEL` | `gpt-4o-mini` | Имя модели на сервере |

**Сохраните файл.** Никогда не выкладывайте `.env` в GitHub.

### 1.5. Автопроверка

```powershell
python -m center_voice_agent.cli.setup_check
```

Должно закончиться текстом **«Проверка пройдена»**.  
Если есть **ОШИБКИ** — исправьте по подсказкам (часто нет `.env` или не тот Python).

### 1.6. Демо без денег за API

```powershell
python -m center_voice_agent.cli.demo_turn
```

В консоли должны появиться JSON-строки с `gateway_in` и `gateway_out`. Это значит: код живой.

### 1.7. Реальная нейросеть (главная проверка)

```powershell
python -m center_voice_agent.cli.live_turn Привет! Кто ты?
```

**Ожидание:** в консоли — нормальный ответ текстом (не ошибка про ключ).

Если ошибка:

- проверьте `LLM_API_KEY`, URL и имя модели;
- спросите у разработчиков API, поддерживает ли модель **вызов инструментов (tools)**.

### 1.8. Тесты (по желанию)

```powershell
python -m pytest tests/ -q
```

Должно быть `passed` без `failed`.

---

## Часть 2. GitHub (15–30 минут)

Код агента лежит в репозитории:  
https://github.com/gorunovaalbina9-droid/arina  
ветка **`center-voice-agent`**, папка **`center_voice_agent/`**.

### Вариант А — проще

1. Откройте в браузере:  
   https://github.com/gorunovaalbina9-droid/arina/compare/master...center-voice-agent  
2. Создайте **Pull Request** и смержите, если GitHub не ругается.

### Вариант B — если push в master не работает

GitHub отклоняет `master`, потому что в истории есть **очень большие файлы** (установщик Арины >100 MB).

**Что можно сделать:**

- Работать в ветке **`center-voice-agent`** (уже есть весь код агента), **или**
- Удалить большие `.exe` / `.zip` из git и пушить снова (нужен опытный разработчик), **или**
- Создать **отдельный** репозиторий только для `center_voice_agent`.

Подробнее: [GIT_PUSH.md](GIT_PUSH.md)

### Залить свои последние правки

```powershell
cd "C:\Users\Альбина\глебебля2"
git add center_voice_agent
git commit -m "обновление center_voice_agent"
git push origin center-voice-agent
```

(Если Git спросит логин — используйте токен GitHub.)

---

## Часть 3. Голосовой помощник «Арина» (voice_assistant)

**Важно:** папка **`13_reber`** в монорепо — это **бот кафе** (Telegram), не голосовой наставник.  
Голос — это **`voice_assistant/`** (окно с микрофоном).

### 3.1. Установить агент как библиотеку

Из активированного venv `center_voice_agent`:

```powershell
pip install -e "C:\Users\Альбина\глебебля2\center_voice_agent"
```

(Путь к `center_voice_agent` — свой.)

### 3.2. Настроить голосовой помощник (опционально)

В `.env` **voice_assistant** (или в переменных окружения) можно добавить:

```env
USE_CENTER_AGENT=true
CENTER_AGENT_ROOT=C:\Users\Альбина\глебебля2\center_voice_agent
```

И **обязательно** должен быть настроен `center_voice_agent\.env` с `LLM_API_KEY`.

Файл-мост уже в репозитории: `voice_assistant/center_agent_bridge.py`.  
Подключение в GUI — следующий шаг разработки; пока проверяйте агента **текстом**:

```powershell
cd center_voice_agent
python -m center_voice_agent.cli.text_turn --live
```

Печатаете фразы с клавиатуры — ответы от реальной модели.

---

## Часть 4. Методист и контент (не программирование)

| Задача | Кто | Где |
|--------|-----|-----|
| Тексты режимов (диалог, урок, игра) | Методист | `config/modes/*.yaml`, инструкция [METHODIST.md](METHODIST.md) |
| Сценарии занятий | Методист | `config/scenarios/*.yaml` |
| Что можно хранить о ребёнке | Юрист + методист | [MEMORY_CATEGORIES.md](MEMORY_CATEGORIES.md) |
| Фразы «переключись в учебный» | Уже в `config/voice/mode_commands.yaml` | при необходимости править |

---

## Часть 5. Перед пилотом с детьми

Чеклист: [PILOT.md](PILOT.md)

Кратко:

- [ ] `live_turn` с вашей моделью работает  
- [ ] Решено, как дети будут говорить с агентом (текст / голос / бот)  
- [ ] Согласованы память и модерация  
- [ ] Есть план, к кому звонить при сбое  

---

## Часть 6. Что вам НЕ нужно делать

- Писать Python-код агента с нуля — уже сделано.  
- Разбираться в LangGraph — можно отключить: `USE_LANGGRAPH=false` в `.env`.  
- Настраивать `13_reber` для наставника — это другой продукт (кафе).

---

## Если что-то сломалось

| Симптом | Что проверить |
|---------|----------------|
| `LLM_API_KEY не задан` | Файл `.env` в папке `center_voice_agent`, не в корне монорепо |
| Предупреждение Pydantic / 3.14 | Пересоздайте venv на 3.12 |
| `pytest` долго | Нормально на Windows; подождите 3–5 минут |
| Push rejected 100 MB | Ветка `center-voice-agent`, см. GIT_PUSH.md |

---

## Контакты в репозитории

- Технические решения: [DECISIONS.md](DECISIONS.md)  
- Мелкие цели: [GOALS.md](GOALS.md)  
- Быстрый чеклист: [SETUP_CHECKLIST.md](SETUP_CHECKLIST.md)
