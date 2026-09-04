@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" call run_install.cmd || exit /b 1
set "TSFILE=.sst_timestamp_archive_extra.tmp"
".venv\Scripts\python.exe" tools\timestamp.py > "%TSFILE%" || exit /b 1
set /p TS=<"%TSFILE%"
del /q "%TSFILE%" >nul 2>&1
if not defined TS set "TS=manual"
set "OUT=outputs_archive_extra_extended_%TS%"
echo [SST] v0.4.1 ALL 127 INPUTS EXTRA_EXTENDED -^> %OUT%
".venv\Scripts\python.exe" run_archive_campaign.py --config configs\archive_extra_extended.json --out-dir "%OUT%" --backend auto %*
set RC=%errorlevel%
echo [SST] %OUT%\ARCHIVE_CONCLUSIONS.md
echo [SST] %OUT%\GATE_CONCLUSIONS.md
exit /b %RC%
