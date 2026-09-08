@echo off
setlocal
cd /d "%~dp0"
call _common.cmd
if errorlevel 1 exit /b 1
"%PY%" -m sst_threaded_hole_falsifier.cli reveal --root . --campaign "outputs/thread_focusing/campaign" --blind "outputs/thread_focusing/blind" --out "outputs/thread_focusing/reveal" --config "config/preset_thread_focusing.json"
exit /b %errorlevel%
