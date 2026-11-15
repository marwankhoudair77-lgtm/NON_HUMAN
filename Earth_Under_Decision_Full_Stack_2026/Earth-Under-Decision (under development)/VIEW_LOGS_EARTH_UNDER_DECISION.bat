@echo off
setlocal
cd /d "%~dp0"
where docker >nul 2>nul
if errorlevel 1 (
  echo Docker Desktop is not installed or not on PATH.
  pause
  exit /b 1
)
docker compose logs -f --tail=150
endlocal
