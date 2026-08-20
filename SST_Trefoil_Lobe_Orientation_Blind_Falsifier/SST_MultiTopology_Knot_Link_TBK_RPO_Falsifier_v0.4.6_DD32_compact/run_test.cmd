@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" call run_install.cmd || exit /b 1
echo [1/2] Legacy trefoil/native smoke...
".venv\Scripts\python.exe" tests\smoke_test.py || exit /b 1
echo [2/2] Multi-topology parser/linking/mode smoke...
".venv\Scripts\python.exe" tests\panel_smoke_test.py || exit /b 1
exit /b 0
