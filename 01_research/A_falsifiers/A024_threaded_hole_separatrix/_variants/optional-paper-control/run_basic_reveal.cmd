@echo off
setlocal
cd /d "%~dp0"
call _common.cmd
if errorlevel 1 exit /b 1
"%PY%" -m sst_threaded_hole_falsifier.cli reveal --root . --campaign "outputs/basic/campaign" --blind "outputs/basic/blind" --out "outputs/basic/reveal" --config "config/preset_basic.json"
exit /b %errorlevel%
