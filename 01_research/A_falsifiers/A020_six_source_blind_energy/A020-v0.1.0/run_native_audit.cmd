@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (echo Missing .venv. Run run_install.cmd first.& exit /b 2)
".venv\Scripts\python.exe" -m native_ext.build_ext_if_needed --force --strict
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" run_native_audit.py --out outputs\native_audit_latest.json --strict
exit /b %errorlevel%
