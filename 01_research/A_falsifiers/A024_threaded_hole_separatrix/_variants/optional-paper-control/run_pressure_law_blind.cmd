@echo off
setlocal
cd /d "%~dp0"
call _common.cmd
if errorlevel 1 exit /b 1
"%PY%" -m sst_threaded_hole_falsifier.cli blind --root . --campaign "outputs/pressure_law/campaign" --out "outputs/pressure_law/blind" --config "config/preset_pressure_law.json"
exit /b %errorlevel%
