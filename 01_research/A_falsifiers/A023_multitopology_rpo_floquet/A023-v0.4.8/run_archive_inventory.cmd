@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" call run_install.cmd || exit /b 1
".venv\Scripts\python.exe" run_archive_campaign.py --inventory-only --out-dir outputs_archive_inventory
exit /b %errorlevel%
