@echo off
setlocal
cd /d "%~dp0"
call _common.cmd
if errorlevel 1 exit /b 1
"%PY%" -m sst_threaded_hole_falsifier.cli blind --root . --campaign "outputs/far_field/campaign" --out "outputs/far_field/blind" --config "config/preset_far_field.json"
exit /b %errorlevel%
