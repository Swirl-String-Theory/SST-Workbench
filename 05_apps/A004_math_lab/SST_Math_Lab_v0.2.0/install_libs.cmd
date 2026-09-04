@echo off
setlocal EnableExtensions
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_libs.ps1"
if errorlevel 1 (
  echo.
  echo ERROR: Dependency installation failed.
  echo Check internet access and rerun install_libs.cmd.
  pause
  exit /b 1
)
exit /b 0
