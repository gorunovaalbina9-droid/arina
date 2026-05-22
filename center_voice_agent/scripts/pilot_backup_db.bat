@echo off
setlocal
cd /d "%~dp0.."
set SRC=data\agent.db
if not exist "%SRC%" (
  echo Нет %SRC% — сначала init_db
  exit /b 1
)
if not exist "data" mkdir data
set DEST=data\backups
if not exist "%DEST%" mkdir "%DEST%"
for /f "tokens=1-3 delims=/:. " %%a in ("%date%") do set D=%%c-%%b-%%a
for /f "tokens=1-2 delims=:." %%a in ("%time%") do set T=%%a%%b
set OUT=%DEST%\agent_%D%_%T%.db
copy /Y "%SRC%" "%OUT%" >nul
echo OK: %OUT%
