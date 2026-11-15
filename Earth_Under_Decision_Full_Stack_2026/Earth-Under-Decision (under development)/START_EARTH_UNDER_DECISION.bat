@echo off
setlocal
cd /d "%~dp0"

echo ================================================
echo       EARTH UNDER DECISION - START
echo ================================================
echo.

where docker >nul 2>nul
if errorlevel 1 (
  echo Docker Desktop is not installed or Docker is not on PATH.
  echo Install Docker Desktop, open it, then run this file again.
  echo https://www.docker.com/products/docker-desktop/
  pause
  exit /b 1
)

docker info >nul 2>nul
if errorlevel 1 (
  echo Docker Desktop is installed but its engine is not running.
  echo Open Docker Desktop, wait until it says Engine running, then try again.
  pause
  exit /b 1
)

if not exist ".env" (
  copy ".env.example" ".env" >nul
  echo Created a placeholder .env file. It contains no real credentials.
)

echo Building and starting the database and website...
docker compose up -d --build
if errorlevel 1 (
  echo.
  echo Startup failed. Recent logs:
  docker compose logs --tail=80
  pause
  exit /b 1
)

echo Waiting for the web service to become ready...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ready=$false; for($i=0; $i -lt 90; $i++){ try { $r=Invoke-WebRequest -UseBasicParsing -Uri 'http://localhost:8000/ready' -TimeoutSec 2; if($r.StatusCode -eq 200){$ready=$true; break} } catch {}; Start-Sleep -Seconds 2 }; if(-not $ready){exit 1}"
if errorlevel 1 (
  echo The containers started, but the web service has not become ready.
  echo Check logs with: docker compose logs -f web
  pause
  exit /b 1
)

start "" "http://localhost:8000"
echo.
echo Website opened: http://localhost:8000
echo API documentation: http://localhost:8000/docs
echo To stop safely, double-click STOP_EARTH_UNDER_DECISION.bat
pause
endlocal
