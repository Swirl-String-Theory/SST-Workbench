@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" call run_install.cmd || exit /b 1
set "TSFILE=.sst_timestamp_extended.tmp"
".venv\Scripts\python.exe" tools\timestamp.py > "%TSFILE%"
if errorlevel 1 (
  echo [FAIL] Could not generate output timestamp.
  exit /b 1
)
set /p TS=<"%TSFILE%"
del /q "%TSFILE%" >nul 2>&1
if not defined TS set "TS=manual"
set "OUT=outputs_extended_%TS%"
echo [SST] EXTENDED blind trefoil test -^> %OUT%
".venv\Scripts\python.exe" run_blind.py --config configs\extended.json --out-dir "%OUT%" --backend auto %*
set RC=%errorlevel%
echo [SST] Result: %OUT%\REPORT.md
echo [SST] Gate conclusions: %OUT%\GATE_CONCLUSIONS.md
exit /b %RC%
