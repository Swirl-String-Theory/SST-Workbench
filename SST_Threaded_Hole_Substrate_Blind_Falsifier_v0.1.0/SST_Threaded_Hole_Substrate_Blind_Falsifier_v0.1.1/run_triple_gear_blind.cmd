@echo off
setlocal
cd /d "%~dp0"
call _common.cmd
if errorlevel 1 exit /b 1
"%PY%" -m sst_threaded_hole_falsifier.cli blind --root . --campaign "outputs/triple_gear/campaign" --out "outputs/triple_gear/blind" --config "config/preset_triple_gear.json"
exit /b %errorlevel%
