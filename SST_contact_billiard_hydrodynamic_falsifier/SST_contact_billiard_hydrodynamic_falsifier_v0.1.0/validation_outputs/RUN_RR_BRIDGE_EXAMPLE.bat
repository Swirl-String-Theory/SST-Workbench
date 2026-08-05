@echo off
setlocal
cd /d "%~dp0"
py -3 -m sstcbhf analyze --input "C:\example\trefoil_polish.txt" --samples 384 --hydro-samples 96 --out "outputs\rr_contact_hydro"
set RC=%ERRORLEVEL%
echo.
if %RC% EQU 0 (
  echo All configured gates passed.
) else (
  echo One or more gates failed or remain unresolved. Exit code %RC%.
)
pause
exit /b %RC%
