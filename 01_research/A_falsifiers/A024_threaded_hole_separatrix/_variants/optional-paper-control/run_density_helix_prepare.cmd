@echo off
setlocal
cd /d "%~dp0"
call _common.cmd
if errorlevel 1 exit /b 1
if exist "outputs\density_helix" rmdir /s /q "outputs\density_helix"
"%PY%" -m sst_threaded_hole_falsifier.cli prepare --root . --out "outputs/density_helix/campaign" --config "config/preset_density_helix.json"
exit /b %errorlevel%
