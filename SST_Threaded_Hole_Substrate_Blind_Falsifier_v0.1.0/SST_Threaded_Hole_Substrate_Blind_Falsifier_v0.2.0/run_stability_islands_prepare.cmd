@echo off
setlocal
cd /d "%~dp0"
call _common.cmd
if errorlevel 1 exit /b 1
if exist "outputs\stability_islands" rmdir /s /q "outputs\stability_islands"
"%PY%" -m sst_threaded_hole_falsifier.cli prepare --root . --out "outputs/stability_islands/campaign" --config "config/preset_stability_islands.json"
exit /b %errorlevel%
