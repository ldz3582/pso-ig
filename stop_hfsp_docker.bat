@echo off
setlocal
cd /d "%~dp0"

where docker >nul 2>nul
if errorlevel 1 (
  echo Docker is not installed or not in PATH.
  pause
  exit /b 1
)

echo Stopping HFSP Docker service...
docker compose down
if errorlevel 1 (
  echo Failed to stop HFSP Docker service.
  pause
  exit /b 1
)

echo HFSP Docker service stopped.
exit /b 0
