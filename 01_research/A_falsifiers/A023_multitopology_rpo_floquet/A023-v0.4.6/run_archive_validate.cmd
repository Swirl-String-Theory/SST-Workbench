@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" call run_install.cmd || exit /b 1
set "OUT=outputs_archive_validation"
echo [SST] Validating every archive input parser/hash...
".venv\Scripts\python.exe" run_archive_campaign.py --validate-only --out-dir "%OUT%"
exit /b %errorlevel%
