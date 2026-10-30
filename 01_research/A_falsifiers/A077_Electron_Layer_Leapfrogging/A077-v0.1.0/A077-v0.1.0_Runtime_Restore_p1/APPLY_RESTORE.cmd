@echo off
setlocal
cd /d "%~dp0"
python repair_runtime.py --instance ".."
if errorlevel 1 (
  echo [RESTORE] REPAIR FAILED - original files left unchanged.
  exit /b 1
)
python repair_runtime.py --instance ".." --verify-only
exit /b %ERRORLEVEL%
