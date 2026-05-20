# Как выложить код на GitHub

Репозиторий: https://github.com/gorunovaalbina9-droid/arina

## Где лежит center_voice_agent

| Ветка | Содержимое |
|-------|------------|
| **`center-voice-agent`** | Полный код агента (рекомендуется) |
| **`master`** | Может **не** содержать агент; push часто **отклоняется** из‑за файлов >100 MB в `voice_assistant/installer_output/` |

## Залить изменения агента

```powershell
cd "C:\Users\Альбина\глебебля2"
git checkout center-voice-agent
git add center_voice_agent .github/workflows/center_voice_agent.yml
git status
git commit -m "обновление center_voice_agent"
git push origin center-voice-agent
```

## Смержить в master

1. Откройте Pull Request: `center-voice-agent` → `master`.
2. Если merge заблокирован из‑за больших файлов в истории `master` — не мержите; работайте в `center-voice-agent`.

## Очистка master (для разработчика)

Нужно убрать из истории git файлы вроде:

- `voice_assistant/installer_output/Арина_Setup.exe`
- `voice_assistant/installer_output/arina_bundle.zip`

Инструменты: `git filter-repo` или BFG Repo-Cleaner. После очистки — force push (осторожно, согласовать с командой).

## Отдельный репозиторий

Альтернатива: экспорт только папки `center_voice_agent` в новый репозиторий без истории монорепо.
