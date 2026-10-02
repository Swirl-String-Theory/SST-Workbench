@echo off
setlocal
cd /d "%~dp0"
call _common.cmd
if errorlevel 1 exit /b 1
if exist "outputs\pressure_law" rmdir /s /q "outputs\pressure_law"
"%PY%" -m sst_threaded_hole_falsifier.cli prepare --root . --out "outputs/pressure_law/campaign" --config "config/preset_pressure_law.json"
exit /b %errorlevel%
