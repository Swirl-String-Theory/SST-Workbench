@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" call run_install.cmd || exit /b 1
set "TSFILE=.sst_timestamp_archive.tmp"
".venv\Scripts\python.exe" tools\timestamp.py > "%TSFILE%" || exit /b 1
set /p TS=<"%TSFILE%"
del /q "%TSFILE%" >nul 2>&1
if not defined TS set "TS=manual"
set "OUT=outputs_archive_survey_%TS%"
echo [SST] v0.4.1 FULL ARCHIVE SURVEY -^> %OUT%
".venv\Scripts\python.exe" run_archive_sweep.py --config configs\panel_survey.json --out-dir "%OUT%" --backend auto %*
exit /b %errorlevel%
