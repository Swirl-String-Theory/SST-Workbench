@echo off
setlocal
cd /d "%~dp0"
call _common.cmd
if errorlevel 1 exit /b 1
"%PY%" -m sst_threaded_hole_falsifier.cli reveal --root . --campaign "outputs/extended/campaign" --blind "outputs/extended/blind" --out "outputs/extended/reveal" --config "config/preset_extended.json"
exit /b %errorlevel%
