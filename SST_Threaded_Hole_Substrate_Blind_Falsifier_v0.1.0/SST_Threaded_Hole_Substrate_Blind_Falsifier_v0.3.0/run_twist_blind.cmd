@echo off
setlocal
cd /d "%~dp0"
call _common.cmd
if errorlevel 1 exit /b 1
"%PY%" -m sst_threaded_hole_falsifier.cli blind --root . --campaign "outputs/twist/campaign" --out "outputs/twist/blind" --config "config/preset_twist.json"
exit /b %errorlevel%
