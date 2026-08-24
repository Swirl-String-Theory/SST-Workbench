@echo off
setlocal EnableExtensions
cd /d "%~dp0" || exit /b 1

set "VENV_DIR=%CD%\.venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"

if not exist "%VENV_PY%" (
    echo [install] Creating local virtual environment: "%VENV_DIR%"
    where py >nul 2>nul
    if not errorlevel 1 (
        py -3 -m venv "%VENV_DIR%"
    ) else (
        where python >nul 2>nul
        if errorlevel 1 (
            echo ERROR: Neither the Windows py launcher nor python.exe was found on PATH.
            endlocal & exit /b 1
        )
        python -m venv "%VENV_DIR%"
    )
    if errorlevel 1 (
        echo ERROR: Failed to create .venv.
        endlocal & exit /b 1
    )
)

if not exist "%VENV_PY%" (
    echo ERROR: Virtual-environment Python not found: "%VENV_PY%"
    endlocal & exit /b 1
)

echo [install] Python: "%VENV_PY%"
"%VENV_PY%" -m pip install --upgrade pip
if errorlevel 1 endlocal & exit /b 1
"%VENV_PY%" -m pip install -r requirements.txt
if errorlevel 1 endlocal & exit /b 1
"%VENV_PY%" -m pip install -e .
if errorlevel 1 endlocal & exit /b 1

endlocal & exit /b 0
