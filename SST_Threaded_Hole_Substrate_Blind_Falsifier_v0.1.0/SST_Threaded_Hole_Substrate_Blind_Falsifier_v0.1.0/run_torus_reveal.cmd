@echo off
setlocal
cd /d "%~dp0"
call _common.cmd
if errorlevel 1 exit /b 1
"%PY%" -m sst_threaded_hole_falsifier.cli reveal --root . --campaign "outputs/torus/campaign" --blind "outputs/torus/blind" --out "outputs/torus/reveal" --config "config/preset_torus.json"
exit /b %errorlevel%
