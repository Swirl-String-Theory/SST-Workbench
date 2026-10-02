@echo off
setlocal
cd /d "%~dp0"
call _common.cmd
if errorlevel 1 exit /b 1
if exist "outputs\far_field" rmdir /s /q "outputs\far_field"
"%PY%" -m sst_threaded_hole_falsifier.cli prepare --root . --out "outputs/far_field/campaign" --config "config/preset_far_field.json"
exit /b %errorlevel%
