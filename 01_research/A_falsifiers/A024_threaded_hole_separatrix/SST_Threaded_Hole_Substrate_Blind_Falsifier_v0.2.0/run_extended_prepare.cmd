@echo off
setlocal
cd /d "%~dp0"
call _common.cmd
if errorlevel 1 exit /b 1
if exist "outputs\extended" rmdir /s /q "outputs\extended"
"%PY%" -m sst_threaded_hole_falsifier.cli prepare --root . --out "outputs/extended/campaign" --config "config/preset_extended.json"
exit /b %errorlevel%
