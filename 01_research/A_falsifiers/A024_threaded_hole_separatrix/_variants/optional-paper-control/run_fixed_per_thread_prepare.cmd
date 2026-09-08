@echo off
setlocal
cd /d "%~dp0"
call _common.cmd
if errorlevel 1 exit /b 1
if exist "outputs\fixed_per_thread" rmdir /s /q "outputs\fixed_per_thread"
"%PY%" -m sst_threaded_hole_falsifier.cli prepare --root . --out "outputs/fixed_per_thread/campaign" --config "config/preset_fixed_per_thread.json"
exit /b %errorlevel%
