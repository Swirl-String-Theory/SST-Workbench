@echo off
rem Shared environment discovery. This file is called by the numbered scripts.
set "ROOT=%~dp0.."
for %%I in ("%ROOT%") do set "ROOT=%%~fI"

if exist "%ROOT%\.venv\Scripts\python.exe" (
    set PY_CMD="%ROOT%\.venv\Scripts\python.exe"
) else (
    where py >nul 2>nul
    if not errorlevel 1 (
        set PY_CMD=py -3
    ) else (
        where python >nul 2>nul
        if not errorlevel 1 set PY_CMD=python
    )
)

if not defined PY_CMD (
    echo [ERROR] Python is niet gevonden.
    echo Installeer Python 3.11 of nieuwer en activeer "Add Python to PATH".
    exit /b 1
)

%PY_CMD% -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)" >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python 3.11 of nieuwer is vereist.
    %PY_CMD% --version
    exit /b 1
)
exit /b 0
