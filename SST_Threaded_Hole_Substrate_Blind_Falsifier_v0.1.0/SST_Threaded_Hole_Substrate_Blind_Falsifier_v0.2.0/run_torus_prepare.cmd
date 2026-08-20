@echo off
setlocal
cd /d "%~dp0"
call _common.cmd
if errorlevel 1 exit /b 1
if exist "outputs\torus" rmdir /s /q "outputs\torus"
"%PY%" -m sst_threaded_hole_falsifier.cli prepare --root . --out "outputs/torus/campaign" --config "config/preset_torus.json"
exit /b %errorlevel%
