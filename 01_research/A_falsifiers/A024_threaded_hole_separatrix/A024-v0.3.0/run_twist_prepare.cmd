@echo off
setlocal
cd /d "%~dp0"
call _common.cmd
if errorlevel 1 exit /b 1
if exist "outputs\twist" rmdir /s /q "outputs\twist"
"%PY%" -m sst_threaded_hole_falsifier.cli prepare --root . --out "outputs/twist/campaign" --config "config/preset_twist.json"
exit /b %errorlevel%
