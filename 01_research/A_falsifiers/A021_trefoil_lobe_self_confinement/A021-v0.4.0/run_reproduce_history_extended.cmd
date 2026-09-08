@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" call run_install.cmd || exit /b 1
echo [SST] Recomputing EXTENDED conclusions for v0.1.0, v0.1.1, v0.2.0 and v0.3.0 from bundled identical inputs...
".venv\Scripts\python.exe" tools\reproduce_history.py --mode extended %*
exit /b %errorlevel%
