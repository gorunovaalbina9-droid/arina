# Git: ветки и публикация кода

Монорепо: [arina](https://github.com/gorunovaalbina9-droid/arina).

## Ветки

| Ветка | Назначение |
|-------|------------|
| **`center-voice-agent`** | **Рабочая ветка** — разработка и приёмка агента (`center_voice_agent/`) |
| `master` | Весь монорепо; `git push origin master` может быть заблокирован файлами >100 MB в **истории** (установщики в `voice_assistant/installer_output/`) |
| `gh-pages` | Сайт / релизы (если используется) |

## Клонирование агента

```bash
git clone -b center-voice-agent https://github.com/gorunovaalbina9-droid/arina.git
cd arina/center_voice_agent
```

Уже есть клон:

```bash
git fetch origin
git checkout center-voice-agent
git pull origin center-voice-agent
```

## Что не коммитить

См. корневой `.gitignore`:

- `*.exe`, крупные `*.zip`, `*_deploy.tar.gz`
- `voice_assistant/installer_output/`
- `center_voice_agent/data/` (локальная SQLite)
- `.env` и секреты

## Pull Request в master

Цели 1–3 агента вливаются через PR **`center-voice-agent` → `master`**.

Если после merge push в `master` падает (GH001, файл >100 MB) — рабочая ветка остаётся **`center-voice-agent`**; очистка истории — отдельная задача (`git filter-repo` / BFG), см. раздел ниже.

## Опционально: починить push в master

1. Согласовать force-push с командой.
2. Удалить из истории пути вроде `voice_assistant/installer_output/` (BFG или `git filter-repo`).
3. `git push --force-with-lease origin master`.

## Опционально: отдельный репозиторий

Экспорт только `center_voice_agent/` в новый репозиторий — чистая история без голосового клиента и установщиков. Пока каноничный код — ветка **`center-voice-agent`** этого монорепо.
