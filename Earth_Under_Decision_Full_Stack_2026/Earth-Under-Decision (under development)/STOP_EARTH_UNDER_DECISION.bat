@echo off
setlocal
cd /d "%~dp0"
echo Stopping Earth Under Decision...
docker compose down
if errorlevel 1 (
  echo Could not stop the containers. Check that Docker Desktop is running.
  pause
  exit /b 1
)
echo Stopped. Your database and uploaded data volumes were preserved.
pause
endlocal
