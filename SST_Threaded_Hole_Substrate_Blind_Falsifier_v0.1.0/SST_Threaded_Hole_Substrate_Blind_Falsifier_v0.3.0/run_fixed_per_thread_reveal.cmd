@echo off
setlocal
cd /d "%~dp0"
call _common.cmd
if errorlevel 1 exit /b 1
"%PY%" -m sst_threaded_hole_falsifier.cli reveal --root . --campaign "outputs/fixed_per_thread/campaign" --blind "outputs/fixed_per_thread/blind" --out "outputs/fixed_per_thread/reveal" --config "config/preset_fixed_per_thread.json"
exit /b %errorlevel%
