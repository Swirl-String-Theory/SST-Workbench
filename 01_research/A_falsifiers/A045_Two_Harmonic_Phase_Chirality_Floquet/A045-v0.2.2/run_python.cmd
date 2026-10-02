@echo off
setlocal
cd /d "%~dp0"
python -m sst_thpcf.campaign --config configs\basic.json --backend python --root . --package
if errorlevel 1 exit /b %errorlevel%
