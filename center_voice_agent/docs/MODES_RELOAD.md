# Перезагрузка режимов (5.3.1)

## CLI (новый процесс)

```powershell
python -m center_voice_agent.cli.reload_modes
```

Обновляет только **этот** процесс Python. Уже запущенный бот — нет.

## В том же процессе (бот / bridge)

```python
ids = await session.reload_modes()
# или
ids = container.mode_registry.reload_all()
```

`AgentSession.reload_modes()` в `integration/bridge.py` вызывает `gateway.modes.reload_all()`.

## После modes_publish

1. `modes_publish ...`
2. `reload_modes` **в процессе бота** или рестарт бота
3. Проверка `demo_turn` / один ход

## HTTP admin (5.3.2)

Отложено. Пока: CLI + рестарт или `session.reload_modes()`.
