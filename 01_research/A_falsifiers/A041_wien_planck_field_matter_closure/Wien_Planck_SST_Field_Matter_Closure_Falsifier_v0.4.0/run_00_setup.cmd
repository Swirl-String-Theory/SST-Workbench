@echo off
setlocal EnableExtensions
pushd "%~dp0" || exit /b 1
set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" (
  echo [setup] Creating local virtual environment...
  py -3 -m venv .venv || goto :fail
)
"%PY%" -m pip install --upgrade pip setuptools wheel || goto :fail
"%PY%" -m pip install -r requirements.txt || goto :fail
popd
exit /b 0
:fail
set "RC=%ERRORLEVEL%"
popd
exit /b %RC%
