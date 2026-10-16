@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" set MODE=SELFTEST
if not "%~1"=="" set MODE=%~1
set INPUT=%~2
if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv || exit /b 1
  .venv\Scripts\python.exe -m pip install --upgrade pip
  .venv\Scripts\python.exe -m pip install -r requirements.txt || exit /b 1
)
if /I "%MODE%"=="SELFTEST" (
  .venv\Scripts\python.exe -m a060.cli SELFTEST
  exit /b %ERRORLEVEL%
)
if "%INPUT%"=="" (
  echo Usage: run_all.cmd BASIC^|FULL path_to_npz_or_directory
  exit /b 2
)
for /f "tokens=1-4 delims=/ " %%a in ("%date%") do set DS=%%d%%b%%c
set TS=%time:~0,2%%time:~3,2%%time:~6,2%
set TS=%TS: =0%
set OUT=outputs\%DS%_%TS%_%MODE%
.venv\Scripts\python.exe -m a060.cli %MODE% "%INPUT%" --out "%OUT%"
exit /b %ERRORLEVEL%
