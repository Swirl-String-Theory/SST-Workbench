@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  py -3 -m venv .venv
  if errorlevel 1 exit /b 1
)
.venv\Scripts\python.exe -m pip install -r requirements.txt -q
if errorlevel 1 exit /b 1
if "%~1"=="" (
  .venv\Scripts\python.exe -m a064.cli BUNDLED
) else (
  .venv\Scripts\python.exe -m a064.cli %*
)
exit /b %errorlevel%
