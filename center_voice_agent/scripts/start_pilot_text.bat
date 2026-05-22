@echo off
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" (
  echo Ошибка: нет .venv. Выполните: py -3.12 -m venv .venv ^& pip install -e ".[dev]"
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
echo Пилот: текстовый чат с агентом. Закройте окно после занятия.
python -m center_voice_agent.cli.text_turn --live
pause
