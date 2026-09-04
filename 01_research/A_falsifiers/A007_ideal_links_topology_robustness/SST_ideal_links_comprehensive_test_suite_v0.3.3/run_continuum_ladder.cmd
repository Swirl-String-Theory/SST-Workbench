@echo off
setlocal EnableExtensions
cd /d "%~dp0"

rem ============================================================
rem SST v0.3.3 continuum ladder launcher
rem
rem Default:
rem   run_continuum_ladder.cmd
rem
rem Modes:
rem   run_continuum_ladder.cmd max
rem   run_continuum_ladder.cmd ladder
rem   run_continuum_ladder.cmd ultra
rem
rem Default links:
rem   L6a4 L4a1 L6n1 L7n2
rem ============================================================

set "MODE=%~1"
if "%MODE%"=="" set "MODE=ladder"

if /I not "%MODE%"=="max" if /I not "%MODE%"=="ladder" if /I not "%MODE%"=="ultra" (
    echo.
    echo ERROR: unknown mode "%MODE%".
    echo Valid modes: max, ladder, ultra
    echo.
    exit /b 2
)

if exist ".venv\Scripts\python.exe" (
    set "PYTHON=.venv\Scripts\python.exe"
) else (
    set "PYTHON=python"
)

echo.
echo ============================================================
echo SST v0.3.3 continuum ladder
echo Mode : %MODE%
echo Links: L6a4 L4a1 L6n1 L7n2
echo Python: %PYTHON%
echo ============================================================
echo.

rem Build/import native backend once, with the same interpreter.
"%PYTHON%" run_native_preflight.py
if errorlevel 1 (
    echo.
    echo ERROR: native preflight failed. No continuum campaign started.
    exit /b %errorlevel%
)

"%PYTHON%" scripts\run_continuum_ladder.py ^
    --mode "%MODE%" ^
    --ids L6a4 L4a1 L6n1 L7n2

set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" (
    echo Continuum ladder completed.
) else (
    echo Continuum ladder ended with error code %RC%.
)
exit /b %RC%
