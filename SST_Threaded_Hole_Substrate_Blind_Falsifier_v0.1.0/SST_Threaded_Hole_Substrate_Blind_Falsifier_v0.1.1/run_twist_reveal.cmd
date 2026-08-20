@echo off
setlocal
cd /d "%~dp0"
call _common.cmd
if errorlevel 1 exit /b 1
"%PY%" -m sst_threaded_hole_falsifier.cli reveal --root . --campaign "outputs/twist/campaign" --blind "outputs/twist/blind" --out "outputs/twist/reveal" --config "config/preset_twist.json"
exit /b %errorlevel%
