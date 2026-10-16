@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (set "MODE=ALL") else (set "MODE=%*")
where py >nul 2>nul
if not errorlevel 1 (
    py -3 -m triadic.entrypoint %MODE%
) else (
    python -m triadic.entrypoint %MODE%
)
set "RC=%ERRORLEVEL%"
echo.
echo PDF location: "%~dp0reports\TRIADIC_CASIMIR_v0.2.0_FALSIFIER_REPORT.pdf"
echo Published PDF: "%~dp0..\Triadic_Casimir_Framework_PKLSA_v0.2.0_FALSIFIER_REPORT.pdf"
exit /b %RC%
