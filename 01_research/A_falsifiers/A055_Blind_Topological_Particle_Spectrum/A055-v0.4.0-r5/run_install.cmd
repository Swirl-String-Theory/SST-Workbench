@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv 2>nul || python -m venv .venv
  if errorlevel 1 exit /b %ERRORLEVEL%
)
set "PY=.venv\Scripts\python.exe"
%PY% -m pip install --upgrade pip setuptools wheel
if errorlevel 1 exit /b %ERRORLEVEL%
%PY% -m pip install -r requirements.txt
exit /b %ERRORLEVEL%
