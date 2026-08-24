@echo off
setlocal EnableExtensions
cd /d "%~dp0"

call run_05_find_input.cmd "%~1"
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" exit /b %RC%

set "INPUT="
for /f "usebackq delims=" %%I in ("build\resolved_input.txt") do if not defined INPUT set "INPUT=%%I"
if not defined INPUT (
  echo ERROR: resolved input path is empty.
  exit /b 4
)

set "PYTHONPATH=%CD%\src;%CD%"
".venv\Scripts\python.exe" preview_dataset.py "%INPUT%" --registry "reference\v0.1.7_seen_canonical64_sha256.json"
set "RC=%ERRORLEVEL%"
exit /b %RC%
