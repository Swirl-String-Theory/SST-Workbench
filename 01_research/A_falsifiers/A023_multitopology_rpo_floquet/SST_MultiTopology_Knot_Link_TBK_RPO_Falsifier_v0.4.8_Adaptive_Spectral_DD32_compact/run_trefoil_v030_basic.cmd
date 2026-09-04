@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo [SST] Running retained v0.3.0 trefoil-specific lobe/TBK gates from historical ZIP...
if not exist ".venv\Scripts\python.exe" call run_install.cmd || exit /b 1
".venv\Scripts\python.exe" tools\reproduce_history.py --mode basic
exit /b %errorlevel%
