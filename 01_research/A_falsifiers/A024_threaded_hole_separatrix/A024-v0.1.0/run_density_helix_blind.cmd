@echo off
setlocal
cd /d "%~dp0"
call _common.cmd
if errorlevel 1 exit /b 1
"%PY%" -m sst_threaded_hole_falsifier.cli blind --root . --campaign "outputs/density_helix/campaign" --out "outputs/density_helix/blind" --config "config/preset_density_helix.json"
exit /b %errorlevel%
