@echo off
setlocal
cd /d "%~dp0"
call _common.cmd
if errorlevel 1 exit /b 1
"%PY%" -m sst_threaded_hole_falsifier.cli reveal --root . --campaign "outputs/triple_gear/campaign" --blind "outputs/triple_gear/blind" --out "outputs/triple_gear/reveal" --config "config/preset_triple_gear.json"
exit /b %errorlevel%
