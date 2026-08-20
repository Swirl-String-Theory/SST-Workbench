@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" call run_install.cmd || exit /b 1
set "TSFILE=.sst_timestamp_panel_basic.tmp"
".venv\Scripts\python.exe" tools\timestamp.py > "%TSFILE%" || exit /b 1
set /p TS=<"%TSFILE%"
del /q "%TSFILE%" >nul 2>&1
if not defined TS set "TS=manual"
set "OUT=outputs_panel_basic_%TS%"
echo [SST] v0.4.5 MULTI-TOPOLOGY BASIC -^> %OUT%
".venv\Scripts\python.exe" run_panel.py --config configs\panel_basic.json --out-dir "%OUT%" --backend auto %*
set RC=%errorlevel%
echo [SST] Report: %OUT%\REPORT.md
echo [SST] Per-gate conclusions: %OUT%\GATE_CONCLUSIONS.md
echo [SST] Comparative conclusions: %OUT%\COMPARATIVE_CONCLUSIONS.md
exit /b %RC%
