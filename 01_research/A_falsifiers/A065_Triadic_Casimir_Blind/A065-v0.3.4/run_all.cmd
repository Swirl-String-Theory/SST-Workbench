@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" run_python.py %*
) else (
    where py >nul 2>nul
    if not errorlevel 1 (
        py -3 run_python.py %*
    ) else (
        python run_python.py %*
    )
)
exit /b %errorlevel%
