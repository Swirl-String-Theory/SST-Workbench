@echo off
setlocal
cd /d "%~dp0"
call _common.cmd
if errorlevel 1 exit /b 1
if exist "outputs\thread_focusing" rmdir /s /q "outputs\thread_focusing"
"%PY%" -m sst_threaded_hole_falsifier.cli prepare --root . --out "outputs/thread_focusing/campaign" --config "config/preset_thread_focusing.json"
exit /b %errorlevel%
