@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if not exist "build" mkdir "build" >nul 2>nul
if exist "build\resolved_input.txt" del /q "build\resolved_input.txt" >nul 2>nul

if exist ".venv\Scripts\python.exe" goto :venv
where py.exe >nul 2>nul
if not errorlevel 1 goto :pylauncher
where python.exe >nul 2>nul
if not errorlevel 1 goto :python
echo ERROR: Python was not found.
exit /b 5

:venv
".venv\Scripts\python.exe" "resolve_input.py" --explicit "%~1" --repo-dir "%CD%" --pattern "*_i10000.txt" --out-file "%CD%\build\resolved_input.txt"
goto :after

:pylauncher
py -3 "resolve_input.py" --explicit "%~1" --repo-dir "%CD%" --pattern "*_i10000.txt" --out-file "%CD%\build\resolved_input.txt"
goto :after

:python
python "resolve_input.py" --explicit "%~1" --repo-dir "%CD%" --pattern "*_i10000.txt" --out-file "%CD%\build\resolved_input.txt"

:after
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
  echo.
  echo INPUT RESOLUTION FAILED with exit code %RC%.
  exit /b %RC%
)

if not exist "build\resolved_input.txt" (
  echo ERROR: resolver returned success but build\resolved_input.txt was not written.
  exit /b 4
)

set "INPUT="
for /f "usebackq delims=" %%I in ("build\resolved_input.txt") do if not defined INPUT set "INPUT=%%I"
if not defined INPUT (
  echo ERROR: resolved input path is empty.
  exit /b 4
)

echo.
echo INPUT RESOLUTION PASS
echo %INPUT%
exit /b 0
