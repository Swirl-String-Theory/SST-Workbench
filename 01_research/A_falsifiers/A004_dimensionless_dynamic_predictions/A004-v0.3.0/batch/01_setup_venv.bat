@echo off
setlocal
call "%~dp0_common.bat"
if errorlevel 1 exit /b 1
cd /d "%ROOT%"

echo === Stap 1: virtuele Python-omgeving ===
if not exist ".venv\Scripts\python.exe" (
    echo Maak .venv aan...
    %PY_CMD% -m venv ".venv"
    if errorlevel 1 goto :fail
) else (
    echo .venv bestaat al; deze wordt hergebruikt.
)

set PY_CMD="%ROOT%\.venv\Scripts\python.exe"
echo === Stap 2: pip en dependencies ===
%PY_CMD% -m pip install --upgrade pip
if errorlevel 1 goto :fail
%PY_CMD% -m pip install -r requirements.txt
if errorlevel 1 goto :fail

 echo === Stap 3: pakket editable installeren ===
%PY_CMD% -m pip install -e .
if errorlevel 1 goto :fail

echo.
echo [OK] Installatie voltooid.
echo Volgende stap: batch\02_selftest.bat
pause
exit /b 0

:fail
echo.
echo [ERROR] Installatie is afgebroken. Bekijk de foutmelding hierboven.
pause
exit /b 1
