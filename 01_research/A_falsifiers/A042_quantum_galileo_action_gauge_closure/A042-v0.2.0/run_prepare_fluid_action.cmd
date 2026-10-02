@echo off
setlocal
cd /d "%~dp0"
call .venv\Scripts\activate.bat
set PYTHONPATH=%CD%
python -m sst_qgi.cli prepare-fluid --config configs\extended.json
if errorlevel 1 exit /b 1
endlocal
