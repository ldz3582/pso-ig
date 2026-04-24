@echo off
setlocal
cd /d "%~dp0"

where docker >nul 2>nul
if errorlevel 1 (
  echo Docker is not installed or not in PATH.
  pause
  exit /b 1
)

docker info >nul 2>nul
if errorlevel 1 (
  echo Docker Desktop is not running.
  pause
  exit /b 1
)

echo Starting HFSP Docker service...
docker compose up --build -d
if errorlevel 1 (
  echo Failed to start HFSP Docker service.
  pause
  exit /b 1
)

start http://127.0.0.1:8000
echo HFSP Docker service is starting on http://127.0.0.1:8000
exit /b 0
