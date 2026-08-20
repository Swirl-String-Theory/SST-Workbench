@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" call run_install.cmd || exit /b 1
for /f %%i in ('".venv\Scripts\python.exe" -c "import datetime;print(datetime.datetime.now().strftime('%%Y%%m%%d_%%H%%M%%S'))"') do set TS=%%i
set "OUT=outputs_basic_%TS%"
echo [SST] BASIC blind trefoil test -^> %OUT%
".venv\Scripts\python.exe" run_blind.py --config configs\basic.json --out-dir "%OUT%" --backend auto %*
set RC=%errorlevel%
echo [SST] Result: %OUT%\REPORT.md
exit /b %RC%
