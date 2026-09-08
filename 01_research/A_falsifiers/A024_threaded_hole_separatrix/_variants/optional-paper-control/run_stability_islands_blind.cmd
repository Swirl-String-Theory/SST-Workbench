@echo off
setlocal
cd /d "%~dp0"
call _common.cmd
if errorlevel 1 exit /b 1
"%PY%" -m sst_threaded_hole_falsifier.cli blind --root . --campaign "outputs/stability_islands/campaign" --out "outputs/stability_islands/blind" --config "config/preset_stability_islands.json"
exit /b %errorlevel%
